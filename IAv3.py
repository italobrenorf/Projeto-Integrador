import mysql.connector
import random
import json
import re

USER_PREFS_FILE = "user_preferences.json"

def conectar_bd():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="receitas_db"
    )

def carregar_alimentos():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM alimentos")
    alimentos = [item[0] for item in cursor.fetchall()]
    conn.close()
    return alimentos

def carregar_preferencias():
    try:
        with open(USER_PREFS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def salvar_preferencias(preferencias):
    with open(USER_PREFS_FILE, "w") as file:
        json.dump(preferencias, file, indent=4)

def processar_resposta(resposta):
    alimentos_desejados = []
    alimentos_nao_desejados = []
    negacoes = ["não", "sem", "evitar", "nunca", "dispensar", "proibido"]
    termos = resposta.lower().split(",")
    
    for termo in termos:
        termo = termo.strip()
        if any(negacao in termo for negacao in negacoes):
            alimento_indesejado = re.sub(r"\b(?:não|sem|evitar|nunca|dispensar|proibido)\b", "", termo).strip()
            alimentos_nao_desejados.append(alimento_indesejado)
        else:
            alimentos_desejados.append(termo)
    
    return alimentos_desejados, alimentos_nao_desejados

def get_recipe_by_ingredient(ingredient):
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    query = """
    SELECT r.id, r.nome, r.categoria, r.cozinha, r.instrucoes
    FROM receitas r
    JOIN ingredientes i ON r.id = i.id_receita
    WHERE i.ingrediente LIKE %s
    """
    cursor.execute(query, (f"%{ingredient}%",))
    receitas = cursor.fetchall()
    conn.close()
    return receitas

def get_ingredientes(receita_id):
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT ingrediente, quantidade FROM ingredientes WHERE id_receita = %s", (receita_id,))
    ingredientes = cursor.fetchall()
    conn.close()
    return ingredientes

def interagir_com_usuario():
    alimentos_permitidos = carregar_alimentos()
    preferencias = carregar_preferencias()
    
    nome_usuario = input("Qual é o seu nome? ").strip().lower()
    
    if nome_usuario in preferencias:
        print("Bem-vindo de volta! Usaremos suas preferências anteriores para recomendações mais precisas.")
        preferencia = preferencias[nome_usuario].get("preferencias", [])
        alergias = preferencias[nome_usuario].get("alergias", [])
    else:
        resposta_preferencias = input("Quais ingredientes você deseja na receita? (Ex: frango, arroz, tomate): ")
        desejados, nao_desejados = processar_resposta(resposta_preferencias)
        preferencias[nome_usuario] = {"preferencias": desejados, "alergias": nao_desejados}
        salvar_preferencias(preferencias)
    
    def buscar_receitas():
        ingrediente_escolhido = random.choice(alimentos_permitidos) if not preferencia else random.choice(preferencia if preferencia else alimentos_permitidos)
        print(f"Buscando receitas com {ingrediente_escolhido}...")
        receitas = get_recipe_by_ingredient(ingrediente_escolhido)
        return [r for r in receitas if receita_valida(r, alergias)]
    
    def receita_valida(receita, alergias):
        ingredientes = get_ingredientes(receita['id'])
        ingredientes_lista = [i['ingrediente'].lower() for i in ingredientes]
        return not any(alergia.strip().lower() in ingredientes_lista for alergia in alergias)
    
    def mostrar_receitas(receitas_validas):
        if receitas_validas:
            print("\nAqui estão algumas sugestões de receitas:")
            for i, receita in enumerate(receitas_validas[:3], 1):
                print(f"{i}. {receita['nome']} - Categoria: {receita['categoria']} | Cozinha: {receita['cozinha']}")
            
            escolha = int(input("\nEscolha a receita que deseja ver (1 a 3) ou 4 para outra sugestão: "))
            
            if escolha == 4:
                mostrar_receitas(buscar_receitas())
            elif 1 <= escolha <= 3:
                receita_escolhida = receitas_validas[escolha - 1]
                print(f"\nVocê escolheu: {receita_escolhida['nome']}")
                print(f"Categoria: {receita_escolhida['categoria']}")
                print(f"Cozinha: {receita_escolhida['cozinha']}")
                print("Ingredientes:")
                for ingrediente in get_ingredientes(receita_escolhida['id']):
                    print(f"- {ingrediente['ingrediente']} ({ingrediente['quantidade']})")
                print("\nModo de preparo:")
                print(receita_escolhida['instrucoes'])
            else:
                print("Opção inválida.")
        else:
            print("Nenhuma receita encontrada sem os ingredientes que causam alergia.")
    
    mostrar_receitas(buscar_receitas())

if __name__ == "__main__":
    interagir_com_usuario()

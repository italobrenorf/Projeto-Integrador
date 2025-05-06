import mysql.connector
import random
import json
from googletrans import Translator

translator = Translator()

USER_PREFS_FILE = "user_preferences.json"

# Conectar ao MySQL
def conectar_bd():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="receitas_db"
    )

# Função para buscar alimentos permitidos
def carregar_alimentos():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM alimentos")
    alimentos = [item[0] for item in cursor.fetchall()]
    conn.close()
    return alimentos

# Função para carregar as preferências do usuário de um arquivo JSON
def carregar_preferencias():
    try:
        with open(USER_PREFS_FILE, "r") as file:
            preferencias = json.load(file)
    except FileNotFoundError:
        preferencias = {}
    return preferencias

# Função para salvar as preferências do usuário em um arquivo JSON
def salvar_preferencias(preferencias):
    with open(USER_PREFS_FILE, "w") as file:
        json.dump(preferencias, file, indent=4)

# Função para traduzir texto utilizando o Google Translate
def traduzir(texto, idioma_destino):
    try:
        resultado = translator.translate(texto, dest=idioma_destino)
        return resultado.text
    except Exception as e:
        print(f"Erro ao traduzir: {e}")
        return texto  # Caso haja erro, retorna o texto original

# Função para buscar receitas pelo ingrediente
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

# Função para buscar ingredientes de uma receita
def get_ingredientes(receita_id):
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT ingrediente, quantidade FROM ingredientes WHERE id_receita = %s", (receita_id,))
    ingredientes = cursor.fetchall()
    conn.close()
    return ingredientes

# Função principal de interação
def interagir_com_usuario():
    alimentos_permitidos = carregar_alimentos()
    preferencias = carregar_preferencias()
    
    nome_usuario = input("Qual é o seu nome? ").strip().lower()
    
    if nome_usuario in preferencias:
        print("Bem-vindo de volta! Usaremos suas preferências anteriores para recomendações mais precisas.")
        preferencia = preferencias[nome_usuario].get("preferencias", [])
        alergias = preferencias[nome_usuario].get("alergias", [])
    else:
        preferencia = input("Quais são suas preferências alimentares? (separe por vírgulas, ou deixe vazio): ").strip().lower().split(",")
        alergias = input("Você possui alergia a algum alimento? (separe por vírgulas, ou deixe vazio): ").strip().lower().split(",")
        preferencias[nome_usuario] = {"preferencias": preferencia, "alergias": alergias}
        salvar_preferencias(preferencias)
    
    def buscar_receitas():
        # Agora, buscar o ingrediente sem tradução
        ingrediente_escolhido = random.choice(alimentos_permitidos) if not preferencia or preferencia == [''] else random.choice(preferencia)
        print(f"Buscando receitas com {ingrediente_escolhido}...")
        
        receitas = get_recipe_by_ingredient(ingrediente_escolhido)
        
        receitas_validas = [r for r in receitas if receita_valida(r, alergias)]
        
        return receitas_validas

    def receita_valida(receita, alergias):
        ingredientes = get_ingredientes(receita['id'])
        ingredientes_lista = [i['ingrediente'].lower() for i in ingredientes]
        
        for alergia in alergias:
            if alergia.strip().lower() in ingredientes_lista:
                return False
        return True

    def mostrar_receitas(receitas_validas):
        if receitas_validas:
            print("\nAqui estão algumas sugestões de receitas:")
            for i, receita in enumerate(receitas_validas[:3], 1):
                print(f"{i}. {receita['nome']} - Categoria: {receita['categoria']} | Cozinha: {receita['cozinha']}")

            escolha = int(input("\nEscolha a receita que deseja ver (1, 2 ou 3) ou 4 para outra sugestão: "))

            if escolha == 4:
                print("Tentando novamente...")
                receitas_validas = buscar_receitas()
                mostrar_receitas(receitas_validas)
            elif 1 <= escolha <= 3:
                receita_escolhida = receitas_validas[escolha - 1]
                print(f"\nVocê escolheu: {receita_escolhida['nome']}")
                print(f"Categoria: {receita_escolhida['categoria']}")
                print(f"Cozinha: {receita_escolhida['cozinha']}")
                print("Ingredientes:")
                ingredientes = get_ingredientes(receita_escolhida['id'])
                for ingrediente in ingredientes:
                    print(f"- {ingrediente['ingrediente']} ({ingrediente['quantidade']})")
                print("\nInstruções de preparo:")
                print(receita_escolhida['instrucoes'])
            else:
                print("Opção inválida.")
        else:
            print("Nenhuma receita encontrada sem os ingredientes que causam alergia.")

    receitas_validas = buscar_receitas()
    mostrar_receitas(receitas_validas)

if __name__ == "__main__":
    interagir_com_usuario()

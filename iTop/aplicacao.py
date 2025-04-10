import unicodedata
from PIL import Image
import pytesseract
import re
import pdfplumber
# import requests

#Calendário
calendario = ["JAN/", "FEV/", "MAR/", "ABR/", "MAI/", "JUN/", "JUL/", "AGO/", "SET/", "OUT/", "NOV/", "DEZ/"]

# Classes e seus respectivos valores
classes = {"monofasico": 30, "bifasico": 50, "trifasico": 100}

#Remove acentos e retorna o texto em minusculo
def trataTexto(texto):
    texto_normalizado = unicodedata.normalize('NFD', texto)
    texto_sem_acentos = ''.join(
        char for char in texto_normalizado
        if unicodedata.category(char) != 'Mn'
    )
    return texto_sem_acentos.lower()

#Função que verifica se existe a classe e retorna o valor a ser abatido pela classe responsável
def verificaClasse(classe):
   for tipo in classes:
        if tipo in trataTexto(classe):
            return classes[tipo]

#Retorna baixa renda ou irrig. noturna, se não retorna a própria subclasse
def verificaSubClasse(subclasse):
    if "baixa renda" in trataTexto(subclasse):
        return "baixa renda"
    elif "irrig. noturna" in trataTexto(subclasse):
        return "irrig. noturna"
    return "nenhuma classe especial"

#Função que calcula a média líquida do consumo de energia
def calculaMediaLiquida(historico, classe):
    valorTotal = 0
    divisor = int(len(historico))

    # Primeiro precisamos verificar o valor do divisor, assim para cada valor zero no final do histórico iremos subtrair uma unidade do divisor
    for valor in reversed(historico):
        if valor == "0": divisor = divisor - 1
        else: break

    for mes in historico:
        #pode haver erros no momento da conversão, fazer o tratamento de erros!!!!
        valorTotal += float(mes)

    try:
        mediaBruta = valorTotal/divisor
    except:
        print("Erro no calculo da media bruta")

    try:
        mediaLiquida = mediaBruta - float(verificaClasse(classe))
        return mediaLiquida
    
    except:
        print("Erro na leitura da classe")
        return

    

def verificarAvisoCorte(avisoCorte):
    if avisoCorte:
        print("Possui aviso de corte")
        return True
    else:
        print("Não possui aviso de corte")
        return False

def possuiGeracao(itensFatura):
    if itensFatura:
        print("possui geração")
        return True
    else:
        print("não possui geração")
        return False
    
def verificaDetalhes(modalidadeTarifaria, subclasse, classe, historico, avisoCorte, itensFatura):
    print("----------------------")
    print("Modalidade: ", modalidadeTarifaria)
    print("Subclasse: ", verificaSubClasse(subclasse))
    print("Classe: ", classe)
    print("Historico: ", historico)
    print("Aviso de corte: ", verificarAvisoCorte(avisoCorte))
    print("Geração própria: ", possuiGeracao(itensFatura))
    print("Média líquida: ", calculaMediaLiquida(historico, classe))
    print("----------------------")

 
#Aprovações (B1, B2, B3 && Não ser baixa renda && Consumo médio líquido acima de 100kwh && não possui aviso de corte) 
#Reprovações (baixa renda || Consumo médio líquido abaixo de 100kwh || possuí aviso de corte e/+ consumo médio líquido abaixo de 500kwh || grupo A + irrignte noturno)
#Exceções (Grupo A || irrigante noturno + grupo B || aviso de corte + consumo médio acima de 501kwh || possui geração própria ou energia por assinatura)

def verificaConta(modalidadeTarifaria, subclasse, classe, historico, avisoCorte, itensFatura):

    if (modalidadeTarifaria) == "grupo a":
        print("+++++++++++++++++++++++++")
        print("Caso de exceção") # TALVEZ
        print("+++++++++++++++++++++++++")
        return respostaProposta("TALVEZ")
        
    

    if classe == "": # Caso em que não conseguimos identificar o tipo da classe, mandamos para o operador
        print("+++++++++++++++++++++++++")
        print("Caso de exceção") # TALVEZ
        print("+++++++++++++++++++++++++")
        return respostaProposta("TALVEZ")
    

    #Aprovação:
    if (modalidadeTarifaria) == "grupo b" and verificaSubClasse(subclasse) != "baixa renda" and calculaMediaLiquida(historico, classe)>=100 and not verificarAvisoCorte(avisoCorte) and verificaSubClasse(subclasse) != "irrig. noturna" and not possuiGeracao(itensFatura):
        print("+++++++++++++++++++++++++")
        print("Aprovação automática") # OK
        print("+++++++++++++++++++++++++")
        return respostaProposta("OK")
        

    #Reprovação:
    if verificaSubClasse(subclasse) == "baixa renda" or calculaMediaLiquida(historico, classe)<100 or (verificarAvisoCorte(avisoCorte) and calculaMediaLiquida(historico, classe)<500) or ((modalidadeTarifaria) == "grupo a" and verificaSubClasse(subclasse) == "irrig. noturna"):
        print("+++++++++++++++++++++++++")
        print("Reprovação automática") # NAO CUMPRE
        print("+++++++++++++++++++++++++")
        return respostaProposta("NAO CUMPRE")
        

    #Exceções:
    if ((modalidadeTarifaria) == "grupo b" and verificaSubClasse(subclasse) == "irrig. noturna") or (verificarAvisoCorte(avisoCorte) and calculaMediaLiquida(historico, classe) > 501) or possuiGeracao(itensFatura):
        print("+++++++++++++++++++++++++")
        print("Caso de exceção") # TALVEZ
        print("+++++++++++++++++++++++++")
        return respostaProposta("TALVEZ")
        

def encurtar_ano(data):
    if '/' in data:
        mes, ano = data.split('/')
        return f"{mes}/{ano[-2:]}"
    return data  # retorna original se não tiver "/"

def capturar_numero_apos_primeiro_espaco(linha):
    partes = linha.split()
    if len(partes) > 1 and partes[1].replace(".", "").isdigit():
        return partes[1]
    return None

# Função principal que executa toda a lógica do negócio
def iniciaArquivo(arquivo):
    texto = ""
    linhas = []

    # Expressão para capturar padrão tipo JAN/2025, FEV/2023 etc.
    padrao = r"\b[A-Z]{3}/\d{4}\b"

    # Expressão para capturar padrão tipo JAN/25, FEV/23 etc.
    padraoCurto = r"\b[A-Z]{3}/\d{2}\b"

    #Histórico de consumo
    historico = ["0", "0","0","0","0","0","0","0","0","0","0","0","0"]

    try:
        with pdfplumber.open(arquivo) as pdf:

            for pagina in pdf.pages:
                texto += pagina.extract_text() + "\n"
                if texto:
                    linhas.extend(texto.splitlines())  # separa por linha
        
        print("processa arquivo")
        return processaArquivo(linhas, historico, padrao, padraoCurto)

    except:
        print("Erro na leitura do arquivo. Certifique-se de ser um arquivo pdf.")
        # Caso em que houve algum problema na leitura do arquivo. O operador deve analisar esse caso separadamente
        print("+++++++++++++++++++++++++")
        print("Caso de exceção") # TALVEZ
        print("+++++++++++++++++++++++++")
        return respostaProposta("TALVEZ")


def processaArquivo(linhas, historico, padrao, padraoCurto):
    modalidadeTarifaria = ""
    classe  = ""
    subclasse = ""
    avisoCorte = ""
    itensFatura = ""
    i = 0
    mesReferenteInicial = ""
    mesReferenteAtual = ""
    capturaValor = False

    # 'linhas' agora é uma lista com cada linha do arquivo
    for linha in linhas:
        linha = linha.strip()  # remove \n e espaços extras
        # print(linha)

        #modalidadeTarifaria
        #Aprovação imediata
        grupoB = ["convencional b1" , "convencional b2", "convencional b3"]

        grupoA = ["verde a1", "azul a1",
                "verde a2", "azul a2",
                "verde a3", "azul a3",
                "verde a3a", "azul a3a",
                "verde a4", "azul a4",
                "verde as", "azul as"]

        #Modalidade Tarifaria (feito)
        if any(texto in trataTexto(linha) for texto in grupoA):
            modalidadeTarifaria = "grupo a"
            break
        elif any(texto in trataTexto(linha) for texto in grupoB):
            modalidadeTarifaria = "grupo b"

        #Classe (feito)
        for chave in classes:
            if chave in trataTexto(linha):
                classe = chave

        #Subclasse (feito)
        classesSelecionadas = ["baixa renda", "irrig. noturna"]
        for item in classesSelecionadas:
            if item in trataTexto(linha):
                subclasse = item

        #Histórico
        if any(mes in linha for mes in calendario):
            
            if mesReferenteInicial == "":
                resultado = re.search(padrao, linha)
                mesReferenteInicial = encurtar_ano(resultado.group())  #Captura o mes referente inicial
                mesReferenteAtual = mesReferenteInicial

            if mesReferenteInicial != "":
                resultado = re.search(padraoCurto, linha) #Captura o mes na linha
                if resultado: 
                    mesReferenteAtual = resultado.group()

        if mesReferenteAtual in linha and capturar_numero_apos_primeiro_espaco(linha):
            capturaValor = capturar_numero_apos_primeiro_espaco(linha)
            valorTratado = capturaValor.replace(".", "")
            historico[i] = valorTratado
            i = i + 1
            continue

        #Aviso corte (feito)
        mensagemCorte = "prev. corte"
        if mensagemCorte in trataTexto(linha): avisoCorte = True

        #Geração (feito)
        geracao = ["energia scee isenta", "energia scee hfp isenta"]
        if any(texto in trataTexto(linha) for texto in geracao):
            itensFatura=True
    
    verificaDetalhes(modalidadeTarifaria, subclasse, classe, historico, avisoCorte, itensFatura)
    return verificaConta(modalidadeTarifaria, subclasse, classe, historico, avisoCorte, itensFatura)

def respostaProposta(resp):
    if resp == "OK":
        print("ok")
        dados=({
            "status": "OK",
            "cod_lead": "16"
        })
        return dados
    elif resp == "TALVEZ":
        print("talvez")
        dados=({
            "status": "TALVEZ",
            "cod_lead": "15"
        })
        print("**********")
        print(dados)
        return dados
    elif resp == "NAO CUMPRE":
        print("nao cumpre")
        dados={
            "status": "NAO CUMPRE",
        }
        return dados
    else:
        dados={
            "status": "TALVEZ",
            "cod_lead": "15"
        }
        return dados

# iniciaArquivo(doc)



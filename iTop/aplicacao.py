import unicodedata
from PIL import Image
import pytesseract
import re
import pdfplumber
import json
from .models import Lead
from pypdf import PdfReader
import os
from django.core.files import File
# import requests

#Calendário
calendario = ["JAN/", "FEV/", "MAR/", "ABR/", "MAI/", "JUN/", "JUL/", "AGO/", "SET/", "OUT/", "NOV/", "DEZ/"]

# Classes e seus respectivos valores
classes = {"monofasico": 30, "bifasico": 50, "trifasico": 100}

mediaBruta = None
mediaLiquida = None

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
    revertido = dict(reversed(list(historico.items())))
    global mediaBruta
    global mediaLiquida

    # Primeiro precisamos verificar o valor do divisor, assim para cada valor zero no final do histórico iremos subtrair uma unidade do divisor
    for chave, valor in revertido.items():
        if valor == 0: divisor = divisor - 1

    for chave, valor in historico.items():
        #pode haver erros no momento da conversão, fazer o tratamento de erros!!!!
        valorTotal += float(valor)

    try:
        mediaBruta = valorTotal/divisor
        # print("media ", mediaBruta)
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
    
def verificaDetalhes(modalidadeTarifaria, subclasse, classe, historico, avisoCorte, itensFatura, nome, pessoaFisica, endereco, numeroCliente, numeroInstalacao, rua, numero, complemento, bairro, cep, cidade, estado, classeVerificacaoConta, ehCEMIG):
    print("----------------------")
    print("Modalidade: ", modalidadeTarifaria)
    print("Subclasse: ", verificaSubClasse(subclasse))
    print("Classe: ", classe)
    print("Historico: ", historico)
    print("Aviso de corte: ", verificarAvisoCorte(avisoCorte))
    print("Geração própria: ", possuiGeracao(itensFatura))
    print("Média líquida: ", calculaMediaLiquida(historico, classe))
    print("Nome: ", nome)
    print("PF: ", pessoaFisica)
    print("Endereço: ", endereco)
    print("Rua: ", rua)
    print("Número: ", numero)
    print("Complemento: ", complemento)
    print("Bairro: ", bairro)
    print("CEP: ", cep)
    print("Cidade: ", cidade)
    print("Estado: ", estado)
    print("Numero cliente: ", numeroCliente)
    print("Numero instalação: ", numeroInstalacao)
    print("Verifica classe para o BD: ", classeVerificacaoConta)
    print("É CEMIG: ", ehCEMIG)
    print("----------------------")

 
#Aprovações (B1, B2, B3 && Não ser baixa renda && Consumo médio líquido acima de 100kwh && não possui aviso de corte) 
#Reprovações (baixa renda || Consumo médio líquido abaixo de 100kwh || possuí aviso de corte e/+ consumo médio líquido abaixo de 500kwh || grupo A + irrignte noturno)
#Exceções (Grupo A || irrigante noturno + grupo B || aviso de corte + consumo médio acima de 501kwh || possui geração própria ou energia por assinatura)

def verificaConta(modalidadeTarifaria, subclasse, classe, historico, avisoCorte, itensFatura):

    #Tratamento de dadoos para a Evernet
    print("Verificando atributos: ", modalidadeTarifaria, subclasse, classe, historico, avisoCorte, itensFatura)

    grupoBAnalisar = ["B1", "B2", "B3"]
    {"verde a1": "A1 Verde", "azul a1": "A1 Azul",
                "verde a2": "A2 Verde", "azul a2": "A2 Azul",
                "verde a3": "A3 Verde", "azul a3": "A3 Azul",
                "verde a3a": "A3a Verde", "azul a3a": "A3a Azul",
                "verde a4": "A4 Verde", "azul a4": "A4 Azul",
                "verde as": "As Verde", "azul as": "As Azul"}
    grupoAAnalisar = ["A1 Verde", "A1 Azul",
                      "A2 Verde", "A2 Azul",
                      "A3 Verde","A3 Azul",
                      "A3a Verde", "A3a Azul",
                      "A4 Verde", "A4 Azul",
                      "As Verde", "As Azul"]


    if (modalidadeTarifaria) in grupoAAnalisar:
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
    if (modalidadeTarifaria) in grupoBAnalisar and verificaSubClasse(subclasse) != "baixa renda" and calculaMediaLiquida(historico, classe)>=100 and not verificarAvisoCorte(avisoCorte) and verificaSubClasse(subclasse) != "irrig. noturna" and not possuiGeracao(itensFatura):
        print("+++++++++++++++++++++++++")
        print("Aprovação automática") # OK
        print("+++++++++++++++++++++++++")
        return respostaProposta("OK")
        

    #Reprovação:
    if verificaSubClasse(subclasse) == "baixa renda" or calculaMediaLiquida(historico, classe)<100 or (verificarAvisoCorte(avisoCorte) and calculaMediaLiquida(historico, classe)<500) or ((modalidadeTarifaria) in grupoAAnalisar and verificaSubClasse(subclasse) == "irrig. noturna"):
        print("+++++++++++++++++++++++++")
        print("Reprovação automática") # NAO CUMPRE
        print("+++++++++++++++++++++++++")
        return respostaProposta("NAO CUMPRE")
        

    #Exceções:
    if ((modalidadeTarifaria) in grupoBAnalisar and verificaSubClasse(subclasse) == "irrig. noturna") or (verificarAvisoCorte(avisoCorte) and calculaMediaLiquida(historico, classe) > 501) or possuiGeracao(itensFatura):
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

def historicoEvernet(historico):
    historicoTratado = {"Jan": "", "Fev": "", "Mar": "", "Abr": "", "Mai": "", "Jun": "", "Jul": "", "Ago": "", "Set": "", "Out": "", "Nov": "", "Dez": ""}
    for mesTratado in historicoTratado:
        for mes in historico:
            if trataTexto(mesTratado) in trataTexto(mes) and historicoTratado[mesTratado] == "":
                historicoTratado[mesTratado] = str(historico[mes])
    return json.dumps(historicoTratado)

# Função principal que executa toda a lógica do negócio
def iniciaArquivo(arquivo, cod_lead, senha, url_imagem_final):

    texto = ""
    linhas = []

    # Expressão para capturar padrão tipo JAN/2025, FEV/2023 etc.
    padrao = r"\b[A-Z]{3}/\d{4}\b"

    # Expressão para capturar padrão tipo JAN/25, FEV/23 etc.
    padraoCurto = r"\b[A-Z]{3}/\d{2}\b"

    #Histórico de consumo
    historico = {}

    #Histórico de consumo para ser enviado a Evernet
    historicoEvernet = {}

    try:

        reader = PdfReader(arquivo)

        if reader.is_encrypted:
            if reader.decrypt(senha):
                print("PDF descriptografado com sucesso.")
        else: print("nao tem senha")

        # Verifica se o arquivo possui senha e tenta abri-lo
        if reader.is_encrypted:
            reader.decrypt(senha)

        texto = ""
        with pdfplumber.open(arquivo) as pdf:

            for pagina in pdf.pages:
                texto += pagina.extract_text() + "\n"
                if texto:
                    linhas.extend(texto.splitlines())  # separa por linha

        
        return processaArquivo(linhas, historico, padrao, padraoCurto, cod_lead, arquivo, senha, url_imagem_final)

    except:
        print("Erro na leitura do arquivo. Certifique-se de ser um arquivo pdf.")
        # Caso em que houve algum problema na leitura do arquivo. O operador deve analisar esse caso separadamente
        print("+++++++++++++++++++++++++")
        print("Caso de exceção") # TALVEZ
        print("+++++++++++++++++++++++++")
        return respostaProposta("TALVEZ")


def processaArquivo(linhas, historico, padrao, padraoCurto, cod_lead, arquivo, conta_energia_senha, url_imagem_final):
    modalidadeTarifaria = ""
    classe  = ""
    classeVerificacaoConta = ""
    verificaClasseBD = False
    subclasse = ""
    avisoCorte = False
    itensFatura = False
    i = 0
    mesReferenteInicial = ""
    mesReferenteAtual = ""
    capturaValor = False
    nome = ""
    enderecoTotal = ""
    nInstalacao = False
    numeroCliente = 0
    numeroInstalacao = 0
    verificaBairro = False
    verificaCEP = False
    cep = ""
    cidade = ""
    estado = ""
    bairro = ""
    ehCEMIG = False
    pessoaFisica = False

    # 'linhas' agora é uma lista com cada linha do arquivo
    for linha in linhas:
        linha = linha.strip()  # remove \n e espaços extras
        # print(linha)

        # Tratamento de dados conforme o banco de dados da Evernet -> captura a modalidade tarifária, classe e subclasse (nessa ordem)
        grupoB1 = []
        grupoB2 = []
        grupoB3 = []
        grupoA4 = []


        #modalidadeTarifaria
        #Aprovação imediata
        grupoB = {"convencional b1": "B1", "convencional b2": "B2", "convencional b3": "B3"}

        grupoA = {"verde a1": "A1 Verde", "azul a1": "A1 Azul",
                "verde a2": "A2 Verde", "azul a2": "A2 Azul",
                "verde a3": "A3 Verde", "azul a3": "A3 Azul",
                "verde a3a": "A3a Verde", "azul a3a": "A3a Azul",
                "verde a4": "A4 Verde", "azul a4": "A4 Azul",
                "verde as": "As Verde", "azul as": "As Azul"}

        #Modalidade Tarifaria
        for chave, valor in grupoA.items():
            if chave in trataTexto(linha):
                modalidadeTarifaria = valor

        for chave, valor in grupoB.items():
            if chave in trataTexto(linha):
                modalidadeTarifaria = valor

        #Classe
        for chave in classes:
            if chave in trataTexto(linha):
                classe = chave

        #Subclasse
        subclassesEspeciais = {"baixa renda": "Baixa Renda", "irrig. noturna": "Irrigante Noturno"}
        for chave, valor in subclassesEspeciais.items():
            if chave in trataTexto(linha):
                subclasse = valor
                # print("subclasse ", subclasse)

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
            historico[mesReferenteAtual] = int(valorTratado)
            # i = i + 1
            continue

        #Aviso corte
        mensagemCorte = "prev. corte"
        if mensagemCorte in trataTexto(linha): avisoCorte = True

        #Geração
        geracao = ["energia scee isenta", "energia scee hfp isenta"]
        if any(texto in trataTexto(linha) for texto in geracao):
            itensFatura=True



        #Captura nome -> próxima linha do cep padrão da CEMIG e antes da palavra padrão: Referente
        linhaNome = r"^(.*?)\s+Referente a Vencimento Valor a pagar"
        resultadoLinhaNome = re.search(linhaNome, linha)
        if resultadoLinhaNome:
            nome = resultadoLinhaNome.group(1)
            # print("nome: ", nome)

        # Captura linha co CEP
        if verificaCEP:
            verificaCEP = False
            linhaCEP = trataTexto(linha)
            encontro = re.search(r'(\d{5}-\d{3})\s+([\w\s]+),\s*([a-zA-Z]{2})', linhaCEP, re.IGNORECASE)
            if encontro:
                cep = encontro.group(1)
                cidade = encontro.group(2).strip()
                estado = encontro.group(3)

        # Captura bairro
        if verificaBairro:
            bairro = trataTexto(linha)
            verificaBairro = False
            verificaCEP = True

        #Captura o endereço
        if enderecoTotal == "":
            enderecoTotal = re.search(r'^(.*?)\s+(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)/\d{4}', linha)
            if enderecoTotal:
                enderecoT = enderecoTotal.group(1)

                #Separa o enderecoT em rua, numero e complemento
                separacaoEndereco = re.match(r'^(.*?)(\d+)\s+(.*)$', enderecoT)
                if separacaoEndereco:
                    rua = separacaoEndereco.group(1).strip()
                    numero = separacaoEndereco.group(2).strip()
                    complemento = separacaoEndereco.group(3).strip()
                    verificaBairro = True # Sinal para ler a proxima linha
                    # print("Rua:", rua)
                    # print("Número:", numero)
                    # print("Complemento:", complemento)

            else: enderecoTotal=""
        

        #Tipo de pessoa, verifica se existe algum cpf na conta
        if "cpf" in trataTexto(linha):
            pessoaFisica = True
            # print("pessoa fisica: ", pessoaFisica)

        # Captura o numero do cliente (pode não ter) e da instalação
        if nInstalacao:
            numeros = re.findall(r'\b\d+\b', linha)
            if len(numeros) == 2:
                numeroCliente = int(numeros[0])
                numeroInstalacao = int(numeros[1])
                # print("numero Cliente: ",numeroCliente)
                # print("numero Instalacao: ",numeroInstalacao)
            elif len(numeros) == 1:
                numeroInstalacao =  int(numeros[0])
                # print("numero Instalacao: ",numeroInstalacao)

            nInstalacao = False

        
        if "da instalacao" in trataTexto(linha):
            nInstalacao = True

        if verificaClasseBD:
            classeVerificacaoConta = linha.strip().split()[0]
            verificaClasseBD = False
    
        # Captura o tipo de classe para lançar no bd
        if "classe subclasse modalidade" in trataTexto(linha):
            verificaClasseBD = True

        # Captura CEMIG
        if "cemig" in trataTexto(linha):
            ehCEMIG = True
    
    # verificaDetalhes(modalidadeTarifaria, subclasse, classe, historico, avisoCorte, itensFatura, nome, pessoaFisica, enderecoT, numeroCliente, numeroInstalacao, rua, numero, complemento, bairro, cep, cidade, estado, classeVerificacaoConta, ehCEMIG)
    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    enviaDadosDB(nome, pessoaFisica, ehCEMIG, modalidadeTarifaria, classeVerificacaoConta, subclasse, classe, rua, numero, complemento, bairro, cep, cidade, estado, numeroCliente, numeroInstalacao, historico, cod_lead, avisoCorte, itensFatura, arquivo, conta_energia_senha, url_imagem_final)
    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    # print("Verificando o historio para a Evernetz ", historicoEvernet(historico))
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



def enviaDadosDB(nome, pessoaFisica, ehCEMIG, modalidadeTarifaria, classeVerificacaoConta, subclasse, classe, rua, numero, complemento, bairro, cep, cidade, estado, numeroCliente, numeroInstalacao, historico, cod_lead, avisoCorte, itensFatura, url_imagem, conta_energia_senha, url_imagem_final):

    calculaMediaLiquida(historico, classe)

    # Dicionário
    codModTarifaria = None

    if modalidadeTarifaria == "B1":
        codModTarifaria = 1
    elif modalidadeTarifaria == "B1" and subclasse == "Baixa Renda":
        codModTarifaria = 2
    elif modalidadeTarifaria == "B2":
        codModTarifaria = 3
    elif modalidadeTarifaria == "B2" and subclasse == "Irrigante Noturno":
        codModTarifaria = 4
    elif modalidadeTarifaria == "B3" and classeVerificacaoConta == "Comercial":
        codModTarifaria = 5
    elif modalidadeTarifaria == "B3" and classeVerificacaoConta == "Industrial":
        codModTarifaria = 6
    elif modalidadeTarifaria == "A4 Verde":
        codModTarifaria = 9
    elif modalidadeTarifaria == "A4 Azul":
        codModTarifaria = 10
    elif modalidadeTarifaria == "A4 Verde" and subclasse == "Irrigante Noturno":
        codModTarifaria = 11
    elif modalidadeTarifaria == "A4 Azul" and subclasse == "Irrigante Noturno":
        codModTarifaria = 12

    if classe == "monofasico":
        codClasse = 1
    elif classe == "bifasico":
        codClasse = 2
    elif classe == "trifasico":
        codClasse = 3

    if pessoaFisica:
        pessoaFisica = "PF"
    else:
        pessoaFisica = "PJ"

    if ehCEMIG:
        ehCEMIG = 1
    else:
        ehCEMIG = 2

    historicoFinal = historicoEvernet(historico)

    global mediaBruta
    global mediaLiquida

    mediaBrutaFinal = round(mediaBruta, 2)
    mediaLiquidaFinal = round(mediaLiquida, 2)

    print("aaaaaaaaaaaaaaaaaa")
    print(avisoCorte)
    print(itensFatura)


    statusTotal = verificaConta(modalidadeTarifaria, subclasse, classe, historico, avisoCorte, itensFatura)
    print(statusTotal)
    status = statusTotal['cod_lead']

    print(nome)
    print(cep)
    print(pessoaFisica)
    print(ehCEMIG)
    print(mediaBrutaFinal)
    print(mediaLiquidaFinal)
    print(historicoFinal)
    print(codClasse)
    print(codModTarifaria)
    print(rua)
    print(numero)
    print(complemento)
    print(bairro)
    print(cidade)
    print(estado)
    print(numeroInstalacao)
    print(numeroCliente)
    print(pessoaFisica)
    print(cod_lead)
    print(status)
    print(url_imagem)
    print(conta_energia_senha)

    # url_imagem = str(numeroInstalacao) + str(cod_lead)
    url_imagem = url_imagem_final


    lead = Lead.objects.create(
        nome=nome,
        cep=cep,
        status=status,
        distribuidora=ehCEMIG,
        kwh_medio=mediaBrutaFinal,
        kwh_media_liquida=mediaLiquidaFinal,
        kwh_historico_consumo=historicoFinal,
        classe=codClasse,
        grupo_tarifario=codModTarifaria,
        endereco=rua,
        numero=numero,
        complemento=complemento,
        bairro=bairro,
        cidade=cidade,
        uf=estado,
        numero_uc=numeroInstalacao,
        numero_cliente=numeroCliente,
        tipo_pessoa = pessoaFisica,
        cod_lead=cod_lead,
        conta_energia= url_imagem,
        conta_energia_senha = conta_energia_senha
    )


# iniciaArquivo("002.pdf")
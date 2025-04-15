from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .aplicacao import iniciaArquivo
import requests

# url_imagem = ""   

def baixar_pdf(url_pdf, caminho_destino="arquivo.pdf"):
    response = requests.get(url_pdf)
    with open(caminho_destino, "wb") as f:
        f.write(response.content)
    return caminho_destino

@api_view(['POST'])
def enviar_imagem(request):

    dados = request.data.get("url_arquivo")
    cod_lead = request.data.get("cod_lead_tmp")
    senha = request.data.get("senha")


    # global url_imagem
    url_imagem = "" 
    url_imagem = dados
    url_imagem_final = dados
    print("Verificando url ", url_imagem)

    # Acessa a url informada no metodo post
    # global url_imagem

    # Tratamento do caso em que não temos o caminho do arquivo
    if url_imagem == '':
        print("Caminho não informado, provavelmente é uma requisição sem o POST")
        return Response(status=404)
    
    try:
        response = requests.get(url_imagem, stream=True)

        if response.status_code == 200 and "application/pdf" in response.headers.get("Content-Type", ""):
            with open("conta.pdf", "wb") as f:
                f.write(response.content)

            print("PDF baixado com sucesso.")
            url_imagem = "conta.pdf"
            print(url_imagem)
            resultado = iniciaArquivo(url_imagem, cod_lead, senha, url_imagem_final)
            # print(resultado)
            # Resetando o caminho da url para não haver conflitos
            print("Acabou de verificar")
            url_imagem = ''
            return Response(resultado, status=200)

        else:
            print("Erro ao baixar o PDF ou tipo de conteúdo inesperado.")
            # Resetando o caminho da url para não haver conflitos
            url_imagem = ''
            return Response({"status": "TALVEZ",
                            "cod_lead": "15"})
    except:
        return Response({"status": "TALVEZ",
                            "cod_lead": "15"})

    

# @api_view(['POST'])
# def receber_imagem(request):
#     dados = request.data.get("url_arquivo")
#     global url_imagem
#     url_imagem = dados
#     print("Verificando url ", url_imagem)
#     return Response(dados, status=200)



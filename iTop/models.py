from django.db import models

# Create your models here.

class Lead(models.Model):
    nome = models.CharField(max_length=255)
    cep = models.CharField(max_length=8)
    status = models.CharField(max_length=2)
    distribuidora = models.CharField(max_length=100)
    kwh_medio = models.FloatField()
    kwh_media_liquida = models.FloatField()
    kwh_historico_consumo = models.TextField()  # ou TextField se preferir
    classe = models.CharField(max_length=100)
    grupo_tarifario = models.CharField(max_length=100)
    endereco = models.CharField(max_length=255)
    numero = models.CharField(max_length=20)
    complemento = models.CharField(max_length=255, null=True, blank=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    uf = models.CharField(max_length=2)
    numero_uc = models.CharField(max_length=50)
    numero_cliente = models.CharField(max_length=50)
    cod_lead = models.CharField(max_length=100, unique=True)
    tipo_pessoa = models.CharField(max_length=2)
    data_criacao = models.DateTimeField(auto_now_add=True)
    conta_energia = models.CharField(max_length=255)
    conta_energia_senha = models.CharField(max_length=255)




    def __str__(self):
        return self.nome
    
    class Meta:
        db_table = 'nz_lead_tmp'
        managed = False


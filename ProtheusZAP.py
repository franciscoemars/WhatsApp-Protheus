"""
Script para envio de mensagens WhattsApp para Vendedores.
Analisando Clientes sem compras a mais de 60 dias.
Realease v02 - 26/03/2023 - by femars

"""
import os
import time
from sqlalchemy import (
    create_engine, func, Table, Column, Integer, String, Boolean, Date, MetaData, select, insert, and_)
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service 
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Variaveis para manipulação de datas e horas seguindo padrao Protheus
now = datetime.now()
date_time = now.strftime("%d/%m/%Y %H:%M:%S")
updatein = now.strftime("%Y%m%d")
time_de = datetime.today() - timedelta(days=90) 
time_de = time_de.strftime("%Y%m%d")
time_limite = datetime.today() - timedelta(days=365)
time_limite = time_limite.strftime("%Y%m%d")

# cria uma conexão com o banco de dados Oracle
engine = create_engine(
    'oracle+cx_oracle://p11:password@192.168.0.1/protheusprod')

# Cria uma sessão para interagir com o banco de dados
Session = sessionmaker(bind=engine)
session = Session()

# Cria uma classe que representa a tabela "motoristas"
Base = declarative_base()

log = open('log.txt', 'a')

global_vends = 0

# Clientes
class SA1(Base):
    __tablename__ = 'SA1010'

    A1_COD = Column(String, primary_key=True)
    A1_LOJA = Column(String)
    A1_NOME = Column(String)
    A1_NREDUZ = Column(String)
    A1_REGUTAM = Column(String)
    A1_VEND = Column(String)
    A1_VEND2 = Column(String)
    A1_MSBLQL = Column(String)
    A1_ULTCOM = Column(String)
    A1_ZZUCONT = Column(String)
    D_E_L_E_T_ = Column(String)
    R_E_C_N_O_ = Column(String)

# Vendedores
class SA3(Base):
    __tablename__ = 'SA3010'

    A3_COD = Column(String, primary_key=True)
    A3_NOME = Column(String)
    A3_NREDUZ = Column(String)
    A3_CEL = Column(String)
    A3_ATIVO = Column(String)
    D_E_L_E_T_ = Column(String)
    R_E_C_N_O_ = Column(String)

# Funcao para atualizar a data do envio de msg (A1_ZZUCONT)
def upd_ucont(cod, loja):
    session.query(SA1).filter(
        SA1.A1_COD == cod, SA1.A1_LOJA == loja).update({SA1.A1_ZZUCONT: updatein})
    session.commit()

# Total de vendedores validados.
def fvend(): #R02
    global global_vends
    # Realizando a consulta e retornando o total em uma variável
    global_vends = (
        session.query(func.count(SA3.A3_COD))
        .filter(SA3.D_E_L_E_T_ == ' ', SA3.A3_ATIVO == 'S').scalar())
    print(f'Total de Vendedores Selecionados: {global_vends}\n') 

# Funcao Principal 
def find_cli():
    sql_SA1 = (
        select(SA1)
        .where(SA1.D_E_L_E_T_ == ' ')
        .where(SA1.A1_MSBLQL == '2')
        .where(SA1.A1_ULTCOM <= time_de) 
        .where(and_(SA1.A1_ULTCOM >= time_limite)) #1.1
        )
    cliente = session.scalars(sql_SA1)
    global global_vends
    fvend()
    vend_anterior = [] #R02
    total_vends = 0
    for resultado in cliente:
        if resultado.A1_ZZUCONT <= time_de and resultado.A1_VEND not in vend_anterior and total_vends <= global_vends:
            vend_anterior.append(str(resultado.A1_VEND))
            total_vends = total_vends + 1
            print(f'Cliente Selecionado: {resultado.A1_COD}{resultado.A1_LOJA} - {resultado.A1_VEND}')
            print(f'Ultimo Contato: {resultado.A1_ZZUCONT} - Ultima Compra: {resultado.A1_ULTCOM}')
            print(f'Vendedores contactados: {vend_anterior}\n')
            log.write(f'\nCOD: {resultado.A1_COD} Loja: {resultado.A1_LOJA}')
            log.write(f'\n{resultado.A1_NOME} - {resultado.A1_ULTCOM}')
            log.write(f'\n{resultado.A1_VEND}')
            vendedor = (
                session.query(SA3)
                .filter(SA3.A3_COD == resultado.A1_VEND).first()
            )
            log.write(f' - {vendedor.A3_NOME} - {vendedor.A3_CEL}')
            log.write(f'\n ')
            a3nome = str(vendedor.A3_NREDUZ).strip()
            try:
                ultcom = datetime.strptime(resultado.A1_ULTCOM, '%Y%m%d')
                ultcom = ultcom.strftime('%d/%m/%Y')
                mensagem = (f"Olá {a3nome}, passando para lembrar que o Cliente {resultado.A1_COD}{resultado.A1_LOJA} - {resultado.A1_NREDUZ} comprou pela última vez em {ultcom}, para mais detalhes acesse: http://intra.cafeutam.com.br:5001/uClient/cliente/{resultado.A1_COD}/{resultado.A1_LOJA}"
                            )
            except:
                mensagem = (f"Olá {a3nome}, passando para lembrar que o Cliente {resultado.A1_COD}{resultado.A1_LOJA} - {resultado.A1_NREDUZ} ainda não realizou nenhuma compra"
                            )
            numero = str(vendedor.A3_CEL)[1:] # Remover o 0 do começo dos celulares
            whattsapp(mensagem, numero) # Funcao para enviars mensagens de fato
            upd_ucont(resultado.A1_COD, resultado.A1_LOJA) # Registrar o contato.
        else:
            if total_vends >= global_vends:
                print(f'Vendedores contactados: {total_vends} de {global_vends}\n' )
                print(f'Vendedores: {vend_anterior}\n')
                print('Fim dos envios...')
                break 
            else:
                print(f'Cliente {resultado.A1_COD}{resultado.A1_LOJA} foi contactado em {resultado.A1_ZZUCONT}')
                print(f'Vendedor {resultado.A1_VEND}')
                print(f'Vendedores contactados: {total_vends}\n' )

def whattsapp(mensagem, numero):
    print("Localizando contato...")
    time.sleep(1)
    SearchInput = driver.find_element(by=By.CSS_SELECTOR, value=".to2l77zo")
    SearchInput.click()
    SearchInput.send_keys(numero)
    try:
        print("Enviando Mensagem...")
        time.sleep(2)
        SearchInput.send_keys(Keys.ENTER)
        Enviar = driver.find_element(by=By.CSS_SELECTOR, value=".\_3Uu1_ .selectable-text")
        Enviar.click()
        Enviar.send_keys(mensagem,Keys.ENTER)
        time.sleep(2)
        driver.refresh()
        log.write(f'\nMensagem enviada')
        time.sleep(10) # Tempo nescessário para o refresh
    except:
        log.write(f'\nNúmero {numero} não encontrado.')
        print("Contato não encontrado... voltando!")
        time.sleep(2)
        driver.find_element(by=By.CSS_SELECTOR, value=".-Jnba > span").click()


# --> Inicio do programa
s=Service('/mnt/c/Users/femars/Documents/GitHub/uZap/chromedriver_linux64/chromedriver')
driver = webdriver.Chrome(service=s)
driver.get("https://web.whatsapp.com")
print("Escanear QR Code, e aperte Enter quando estiver pronto")
driver.implicitly_wait(0.5)
input()
print("Conectando...")

# Let's Go!!!
find_cli()


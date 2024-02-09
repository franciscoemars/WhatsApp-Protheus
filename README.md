# WhatsApp-Protheus
Script Simples para enviar automaticamente mensagens via WhatsApp utilizando Base de Dados do Protheus.

Acessando as tabelas principais SA1010 (Clientes) e SA3010 (Vendedores), ele busca o cliente que não teve 
compras nos ultimos X dias, depois que selecionou o cliente ele busca o vendedor desse cliente para então
enviar a mensagem para o vendedor com os dados do seu cliente que não está comprando. 

Foi criado um campo personalizado que registra quando a mensagem foi enviada
para não enviar novamente na próxima execução do Script.

Obs. De tempos em tempos o código da pagina do WhatsApp Web é modificado, então é necessário reajustar a parte do Selenium. 

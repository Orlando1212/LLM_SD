# Usar a imagem oficial do Python
FROM python:3.9

# Definir diretório de trabalho dentro do container
WORKDIR /app

# Copiar arquivos para dentro do container
COPY . /app

# Instalar dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expor a porta do Flask
EXPOSE 5000

# Comando para rodar a aplicação
CMD ["python", "app.py"]

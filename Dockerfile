# Usar uma imagem do Python com suporte para Flask
FROM python:3.9

# Definir o diretório de trabalho dentro do contêiner
WORKDIR /app

# Instalar dependências do sistema necessárias para OpenCV e outras bibliotecas
RUN apt-get update && apt-get install -y libgl1-mesa-glx 

# Copiar arquivos para dentro do contêiner
COPY . .

# Instalar as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Tornar o script executável
RUN chmod +x app.py

# Definir a variável de ambiente do Flask
ENV FLASK_APP=app.py

# Exportar a variável de ambiente corretamente
ENTRYPOINT ["sh", "-c", "export FAL_KEY=$FAL_API_KEY && flask run --host=0.0.0.0 --port=5000"]

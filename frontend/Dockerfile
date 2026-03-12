# Używamy lekkiego obrazu Node.js
FROM node:18-alpine

# Ustawiamy katalog roboczy
WORKDIR /app

# Kopiujemy package.json i instalujemy zależności
COPY package.json ./
RUN npm install

# Kopiujemy resztę kodu (katalog src i public)
COPY . .

# Wystawiamy port
EXPOSE 3000

# Uruchamiamy aplikację
CMD ["npm", "start"]
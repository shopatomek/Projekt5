#!/bin/bash
# scripts/clean-dashboard-secrets.sh

set -e

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🧹 Czyszczenie danych osobowych z dashboardów Metabase...${NC}"

# DOSTOSUJ TE LINIE DO SWOICH DANYCH
YOUR_EMAIL="shopa.tomek@gmail.com"
YOUR_NAME="Tomasz Szopa"
YOUR_FIRST_NAME="Tomasz"
YOUR_LAST_NAME="Szopa"
YOUR_USERNAME="tomasz"
YOUR_OLD_EMAIL="shopa.tomek@gmail.com"

FILES=(
    "metabase/dashboards/Market_Daily_Overview.json"
    "metabase/dashboards/dbt_Analytics_Dashboard.json"
)

for FILE in "${FILES[@]}"; do
    if [ -f "$FILE" ]; then
        echo -e "${YELLOW}📄 Przetwarzanie: $FILE${NC}"
        
        # Zamień email
        sed -i "s/$YOUR_EMAIL/admin@dashboard.local/g" "$FILE"
        sed -i "s/$YOUR_OLD_EMAIL/admin@dashboard.local/g" "$FILE"
        
        # Zamień imię i nazwisko (różne warianty)
        sed -i "s/$YOUR_NAME/Admin User/g" "$FILE"
        sed -i "s/$YOUR_FIRST_NAME $YOUR_LAST_NAME/Admin User/g" "$FILE"
        sed -i "s/$YOUR_FIRST_NAME/Admin/g" "$FILE"
        sed -i "s/$YOUR_LAST_NAME/User/g" "$FILE"
        sed -i "s/$YOUR_USERNAME/admin/g" "$FILE"
        
        # Zamień wszystkie emaile w polach "email"
        sed -i 's/"email": "[^"]*"/"email": "admin@dashboard.local"/g' "$FILE"
        
        # Zamień nazwy użytkowników w polach "name", "creator", "updater"
        sed -i 's/"name": "[^"]*"/"name": "Admin"/g' "$FILE"
        sed -i 's/"creator": "[^"]*"/"creator": "Admin"/g' "$FILE"
        sed -i 's/"updater": "[^"]*"/"updater": "Admin"/g' "$FILE"
        sed -i 's/"created_by": "[^"]*"/"created_by": "Admin"/g' "$FILE"
        
        # Zamień ID użytkownika na 1
        sed -i 's/"creator_id": [0-9]\+/"creator_id": 1/g' "$FILE"
        sed -i 's/"updater_id": [0-9]\+/"updater_id": 1/g' "$FILE"
        sed -i 's/"user_id": [0-9]\+/"user_id": 1/g' "$FILE"
        
        echo -e "${GREEN}✅ Oczyszczono: $FILE${NC}"
    else
        echo -e "${RED}❌ Plik nie istnieje: $FILE${NC}"
    fi
done

# Dodatkowe czyszczenie wszystkich plików JSON w folderze
for FILE in metabase/dashboards/*.json; do
    if [ -f "$FILE" ]; then
        # Usuń wszelkie ślady emaili
        sed -i 's/[a-zA-Z0-9._%+-]\+@[a-zA-Z0-9.-]\+\.[a-zA-Z]\{2,\}/admin@dashboard.local/g' "$FILE"
        
        # Usuń ślady imion i nazwisk (popularne polskie imiona)
        sed -i 's/Tomasz/Admin/gI' "$FILE"
        sed -i 's/Szopa/User/gI' "$FILE"
        sed -i 's/tomasz/admin/gI' "$FILE"
        sed -i 's/szopa/user/gI' "$FILE"
    fi
done

echo -e "${GREEN}✅ Czyszczenie zakończone!${NC}"
docker build -t vms-chatbot .
docker run -p 8000:8000 vms-chatbot
docker-compose up --build

docker-compose up -d

Run dev:
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

Run prod:
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
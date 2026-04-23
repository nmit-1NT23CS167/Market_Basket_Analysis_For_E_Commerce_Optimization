#!/bin/bash
# Docker Startup Script for IntelliGrocery PostgreSQL + pgAdmin4
# Usage: ./docker-startup.sh [start|stop|restart|clean]

set -e

PROJECT_NAME="intelligrocery"
COMPOSE_FILE="docker-compose.yml"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Functions
start() {
    echo -e "${BLUE}🚀 Starting IntelliGrocery services...${NC}"
    docker-compose up -d
    sleep 5
    
    echo -e "${GREEN}✅ Services started!${NC}"
    echo ""
    echo -e "${BLUE}📍 Access Points:${NC}"
    echo "   🐘 PostgreSQL:  localhost:5432"
    echo "   🔧 pgAdmin4:    http://localhost:5050"
    echo "   🎯 Streamlit:   http://localhost:8501"
    echo ""
    echo -e "${BLUE}🔑 Credentials:${NC}"
    echo "   PostgreSQL - User: intelligrocery, Pass: IntelliGrocery@2024"
    echo "   pgAdmin4   - Email: admin@intelligrocery.local, Pass: AdminPass@2024"
    echo ""
    echo -e "${BLUE}📝 Next step:${NC}"
    echo "   streamlit run frontend/app.py"
}

stop() {
    echo -e "${BLUE}🛑 Stopping IntelliGrocery services...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ Services stopped!${NC}"
}

restart() {
    echo -e "${BLUE}🔄 Restarting IntelliGrocery services...${NC}"
    stop
    sleep 2
    start
}

clean() {
    echo -e "${RED}⚠️  WARNING: This will delete all data!${NC}"
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}🧹 Cleaning up all data...${NC}"
        docker-compose down -v
        echo -e "${GREEN}✅ Cleanup complete!${NC}"
    else
        echo "Cancelled."
    fi
}

status() {
    echo -e "${BLUE}📊 Container Status:${NC}"
    docker-compose ps
    echo ""
    echo -e "${BLUE}📊 Database Info:${NC}"
    if docker-compose ps -q postgres &>/dev/null; then
        docker exec intelligrocery_db psql -U intelligrocery -d intelligrocery -c "\l"
    else
        echo "PostgreSQL container not running"
    fi
}

logs() {
    service=$1
    if [ -z "$service" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f $service
    fi
}

# Main
case "${1:-start}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    clean)
        clean
        ;;
    status)
        status
        ;;
    logs)
        logs $2
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|clean|status|logs [service]}"
        echo ""
        echo "Commands:"
        echo "  start    - Start all services (PostgreSQL, pgAdmin4)"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  clean    - Delete all data and containers (⚠️  WARNING)"
        echo "  status   - Show container status"
        echo "  logs     - Show service logs (optionally: postgres, pgadmin)"
        echo ""
        echo "Examples:"
        echo "  ./docker-startup.sh start"
        echo "  ./docker-startup.sh logs postgres"
        echo "  ./docker-startup.sh status"
        exit 1
        ;;
esac


# Binary Battle - Backend  

Binary Battle is a real-time competitive coding platform where users can challenge friends, solve coding problems, and compete in live coding duels. This backend manages user authentication, real-time interactions, and secure code execution.  

## Features  

- **Real-Time Challenge Rooms**: WebSocket-based communication for live coding challenges.  
- **Secure Code Execution**: Runs user-submitted code inside isolated Docker containers.  
- **Matchmaking & Leaderboard**: Track user performance and display rankings.  
- **Chat & Messaging**: Integrated chat feature for communication during challenges.  
- **Scalable Architecture**: Redis-based caching and queueing for performance optimization.  

## Tech Stack  

- **Backend**: Django, Django Channels  
- **Database**: PostgreSQL  
- **Real-Time Communication**: WebSockets (Django Channels)  
- **Caching & Message Queue**: Redis  
- **Code Execution**: Docker-based sandboxing  

## Installation  

1. Clone the repository:  
   ```sh
   git clone https://github.com/yourusername/binary-battle-backend.git  
   cd binary-battle-backend  
   ```  

2. Set up a virtual environment and install dependencies:  
   ```sh
   python -m venv venv  
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`  
   pip install -r requirements.txt  
   ```  

3. Configure environment variables in a `.env` file:  
   ```
   DATABASE_URL=your_postgresql_database_url  
   REDIS_URL=your_redis_instance_url  

   ```  

4. Run database migrations:  
   ```sh
   python manage.py migrate  
   ```  

5. Start the server using Uvicorn:  
   ```sh
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload  
   ```  

# Tourism OLAP

**To initialize Database**
1. Start Docker and make sure Docker Engine is running
2. Run command `docker compose up -d`

**To open database in pgAdmin4 use the following credentials**
- Host name: `localhost`
- Port: `5431`
- Username: `postgres`
- Password: `postgres`
- Database name: `stadvdb_db`

**To run Dashboard**
1. Initialize the database
2. Open a terminal in the `./olap-dashboard` directory and run the command `node server.js`
3. Open a new terminal in the same `./olap-dashboard` directory and run the `npm install` and `npm run dev` commands
4. Open browser to http://localhost:5173/

# Private Notes

### How to Start Web app
1. Launch EC2 instance from AWS.
2. Check to see if Public IP has changed, if so, update the IP in the following locations:
   - README
   - static/js/script.js
   - Postman API tests
3. Once EC2 instance is running, access the instance through terminal using: ```ssh -i LeaguePool.pem ubuntu@<Public IP>```. Make sure you are in the Personal Directory.
4. Launch database using the ```sudo systemctl start mongod``` command. (Verify it is running with ```sudo systemctl status mongod```)
4. Finally launch the flask server using ```python3 app.py```
5. Now, you should be able to navigate to the URL listed in the README

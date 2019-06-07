# Dockermon

Monitor which containers are talking to which via tcpdump parsing 

Setup:
```bash
# create a virtualenv (or use conda, whatevers clever)
virtualenv venv
source venv/bin/activate

# pip install some stuff
pip install -r requirement.txt

# build the frontend 
cd dockermon-ui && yarn && yarn build && cd ..
# if you don't have yarn (you should really get yarn)
cd dockermon-ui && npm i && npm run build && cd ..

# run the app
python app.py
```

NOTE: 
Built this for a Hackathon a few months ago and I just used it today, so I guess it's useful after all. I don't quite remember all the setup steps required though...
I will update the docs soon after I play with it some more ;)

Also the UI is not good... doesn't really explain how to use the tool. Maybe I can fix that soon too. 


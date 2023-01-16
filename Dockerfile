FROM mono
 
RUN apt update
RUN apt install python3 python3-pip -y
RUN pip3 install pyinstaller==3.6
RUN mkdir app
COPY program app/.
WORKDIR app
RUN pip3 install -r requirements.txt
RUN pyinstaller --onefile lottery.py -p .
RUN touch this.ext

ENTRYPOINT ["python3", "test.py"]

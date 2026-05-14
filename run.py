from app import create_app #bring in the function that builds my Flask website

app = create_app() #build my website

if __name__ == "__main__": #only run the code below if I started this file directly (another file might import run.py and accidentally start)
    #start running my website in the browser
    app.run(debug=True) #turns on Flask debug mode (shows detailed error messages, exp: TemplateNotFound, SyntaxError)
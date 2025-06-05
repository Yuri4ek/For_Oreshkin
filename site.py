from flask import Flask, render_template

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@app.route('/')
@app.route('/index')
def display():
    return render_template('index.html')


@app.route('/reviews')
def reviews():
    return render_template('reviews.html')


def main():
    app.run(debug=True, port=8080, host='127.0.0.1')


if __name__ == '__main__':
    main()

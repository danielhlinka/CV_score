from flask import Flask, request, render_template
from pipeline.parser import parse_cv
from pipeline.job_parser import parse_job
from pipeline.matcher import match
from pipeline.embedder import enrich_cv

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/score', methods=['POST'])
def score():
    job_profile = parse_job(request.form)
    cv_file     = request.files['cv']
    cv_profile  = parse_cv(cv_file)
    cv_profile  = enrich_cv(cv_profile)
    result      = match(cv_profile, job_profile)
    return render_template('results.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
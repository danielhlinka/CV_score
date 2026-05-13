import os
import logging
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
from pipeline.extractor import extract_text
from pipeline.parser import parse_cv
from pipeline.embedder import enrich_cv
from pipeline.job_parser import parse_job
from pipeline.matcher import match
from pipeline.explainer import explain
from pipeline.sanity_check import sanity_check

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


UPLOAD_FOLDER = "upload"


@app.route('/score', methods=['POST'])
def score():
    job_profile = parse_job(request.form)

    cv_file = request.files['cv']
    filename = secure_filename(cv_file.filename)
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    cv_file.save(save_path)
    raw_text = extract_text(save_path)
    cv_profile = parse_cv(raw_text)
    cv_profile = enrich_cv(cv_profile)

    result = match(cv_profile, job_profile)
    sanity_check(result)
    result["explanation"] = explain(result)

    return render_template('results.html', result=result)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
from flask import Flask, render_template, request, redirect, url_for
import boto3
import os
import uuid


app = Flask(__name__)
 
 # Définir les clés d'accès AWS_ACCESS_KEY_ID et AWS_SECRET_ACCESS_KEY
aws_access_key_id = 'AKIAW3MEFMBBXQEKVKXI'
aws_secret_access_key = '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'

# Configurer le client S3 en utilisant les clés d'accès définies
s3 = boto3.client('s3', 
                  aws_access_key_id=aws_access_key_id, 
                  aws_secret_access_key=aws_secret_access_key,config=boto3.session.Config(signature_version='s3v4'))

# Chemin de stockage local pour les fichiers temporaires téléchargés
UPLOAD_FOLDER = 'C:\\Users\\hp\\Desktop\\tempcloud'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def generer_nom_unique(extension):
    # Générer un nom de fichier unique en utilisant UUID
    return str(uuid.uuid4()) + extension

@app.route('/')
def index():
    # Lister les objets dans le bucket S3
    objets_s3 = lister_objets('sibd2024')
    return render_template('index.html', objets_s3=objets_s3)

@app.route('/uploader', methods=['POST'])
def uploader():
    if 'file' not in request.files:
        return redirect(request.url)
    fichier = request.files['file']
    if fichier.filename == '':
        return redirect(request.url)
    if fichier:
        # Extraire l'extension du fichier
        extension = os.path.splitext(fichier.filename)[1]
        # Générer un nom de fichier unique avec l'extension
        nom_objet = os.path.splitext(fichier.filename)[0]+generer_nom_unique(extension)
        
        chemin_local_temp = os.path.join(app.config['UPLOAD_FOLDER'], nom_objet)
        fichier.save(chemin_local_temp)
        # Uploader le fichier vers le bucket S3 avec un nom unique
        uploader_fichier('sibd2024', nom_objet, chemin_local_temp)
        # Supprimer le fichier temporaire local après l'avoir téléchargé
        os.remove(chemin_local_temp)
        return redirect(url_for('index'))

def lister_objets(bucket_name):
    try:
        # Récupérer la liste des objets dans le bucket
        response = s3.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            objets = [obj['Key'] for obj in response['Contents']]
            return objets
        else:
            return []
    except Exception as e:
        print(f"Erreur lors de la récupération des objets dans le bucket : {str(e)}")
        return []

@app.route('/telecharger', methods=['POST'])
def telecharger():
    objet = request.form.get('objet')
    if objet:
        chemin_local = os.path.join(app.config['UPLOAD_FOLDER'], objet)
        try:
            # Télécharger le fichier depuis S3 vers le système local
            s3.download_file('sibd2024', objet, chemin_local)
            print(f"Fichier {objet} téléchargé avec succès depuis S3 vers {chemin_local}")
        except Exception as e:
            print(f"Erreur lors du téléchargement du fichier depuis S3 : {str(e)}")
    return redirect(url_for('index'))
@app.route('/supprimer/<objet>', methods=['POST'])
def supprimer_objet(objet):
    try:
        # Supprimer l'objet du bucket S3
        s3.delete_object(Bucket='sibd2024', Key=objet)
        print(f"L'objet {objet} a été supprimé avec succès.")
    except Exception as e:
        print(f"Erreur lors de la suppression de l'objet {objet} : {str(e)}")
    return redirect(url_for('index'))


def uploader_fichier(bucket_name, nom_objet, chemin_local):
    try:
        # Uploader le fichier vers le bucket
        s3.upload_file(chemin_local, bucket_name, nom_objet)
        print(f"Fichier {nom_objet} téléchargé avec succès vers le bucket {bucket_name}")
    except Exception as e:
        print(f"Erreur lors du téléchargement du fichier vers le bucket : {str(e)}")

if __name__ == "__main__":
    app.run(debug=True)
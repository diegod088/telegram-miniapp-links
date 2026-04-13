import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from models import SessionLocal, init_db, Enlace, Publicacion, Categoria, CalificacionReporte, Usuario
import datetime
from sqlalchemy import func

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/links', methods=['GET'])
def get_links():
    search = request.args.get('search', '')
    category = request.args.get('category', 'Todas')
    timeframe = request.args.get('timeframe', '')
    sort = request.args.get('sort', 'recent')
    
    db = SessionLocal()
    
    # Subquery for Likes and Dislikes
    like_count = db.query(CalificacionReporte.publicacion_id, func.count('*').label('c')).filter(CalificacionReporte.tipo == 'like').group_by(CalificacionReporte.publicacion_id).subquery()
    dislike_count = db.query(CalificacionReporte.publicacion_id, func.count('*').label('c')).filter(CalificacionReporte.tipo == 'dislike').group_by(CalificacionReporte.publicacion_id).subquery()
    
    query = db.query(Publicacion, Enlace, Categoria, like_count.c.c.label('likes'), dislike_count.c.c.label('dislikes')).select_from(Publicacion)\
        .join(Enlace, Publicacion.enlace_id == Enlace.id)\
        .join(Categoria, Enlace.categoria_id == Categoria.id)\
        .outerjoin(like_count, Publicacion.id == like_count.c.publicacion_id)\
        .outerjoin(dislike_count, Publicacion.id == dislike_count.c.publicacion_id)

    if category != 'Todas':
        query = query.filter(Categoria.nombre_categoria == category)
        
    if search:
        search_filter = f"%{search}%"
        query = query.filter((Enlace.titulo.ilike(search_filter)) | (Enlace.url.ilike(search_filter)) | (Enlace.descripcion.ilike(search_filter)))
        
    if timeframe:
        d = datetime.datetime.utcnow()
        if timeframe == '24h': d -= datetime.timedelta(days=1)
        elif timeframe == '3d': d -= datetime.timedelta(days=3)
        elif timeframe == '7d': d -= datetime.timedelta(days=7)
        elif timeframe == '1m': d -= datetime.timedelta(days=30)
        query = query.filter(Publicacion.fecha_hora_publicacion >= d)
        
    if sort == 'popular':
        query = query.order_by(like_count.c.c.desc().nulls_last())
    else:
        query = query.order_by(Publicacion.fecha_hora_publicacion.desc())
        
    query = query.limit(50)
    results = query.all()
    
    data = []
    for pub, enc, cat, likes, dislikes in results:
        data.append({
            "pub_id": pub.id,
            "url": enc.url,
            "titulo": enc.titulo,
            "descripcion": enc.descripcion,
            "nombre_categoria": cat.nombre_categoria,
            "fecha_hora_publicacion": pub.fecha_hora_publicacion.isoformat() + "Z",
            "likes": likes or 0,
            "dislikes": dislikes or 0
        })
        
    db.close()
    return jsonify(data)

@app.route('/api/rate', methods=['POST'])
def rate_link():
    data = request.json
    pub_id = data.get('pubId')
    tipo = data.get('type') # 'like', 'dislike', 'report_inap'
    tg_user_id = data.get('telegramUserId')
    
    if not pub_id or not tipo or not tg_user_id:
        return jsonify({"error": "Faltan datos"}), 400
        
    db = SessionLocal()
    user = db.query(Usuario).filter_by(telegram_user_id=tg_user_id).first()
    if not user:
        user = Usuario(telegram_user_id=tg_user_id, username='webapp')
        db.add(user)
        db.flush()
        
    exist = db.query(CalificacionReporte).filter_by(publicacion_id=pub_id, usuario_calificador_id=user.id, tipo=tipo).first()
    if exist:
        db.close()
        return jsonify({"error": "Ya registrado"}), 400
        
    db.add(CalificacionReporte(publicacion_id=pub_id, usuario_calificador_id=user.id, tipo=tipo))
    db.commit()
    db.close()
    
    return jsonify({"success": True})

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.path.exists(os.path.join(os.path.dirname(__file__), 'database.db')):
        init_db()
        print("Database initialized.")
        
    port = int(os.getenv('PORT', 3000))
    app.run(port=port, host='0.0.0.0')

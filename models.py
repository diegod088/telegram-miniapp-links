import os
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class Usuario(Base):
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    fecha_registro = Column(DateTime, default=datetime.datetime.utcnow)
    baneado = Column(Boolean, default=False)
    motivo_baneo = Column(Text)
    daily_count = Column(Integer, default=0)
    last_reset = Column(DateTime)
    
    publicaciones = relationship('Publicacion', back_populates='publicador')

class Categoria(Base):
    __tablename__ = 'categorias'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre_categoria = Column(String(100), unique=True, nullable=False)
    
    enlaces = relationship('Enlace', back_populates='categoria')

class Enlace(Base):
    __tablename__ = 'enlaces'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(Text, unique=True, nullable=False)
    titulo = Column(String(255))
    descripcion = Column(Text)
    categoria_id = Column(Integer, ForeignKey('categorias.id'), nullable=False)
    fecha_primera_publicacion = Column(DateTime, default=datetime.datetime.utcnow)
    
    categoria = relationship('Categoria', back_populates='enlaces')
    publicaciones = relationship('Publicacion', back_populates='enlace')

class Publicacion(Base):
    __tablename__ = 'publicaciones'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    enlace_id = Column(Integer, ForeignKey('enlaces.id'), nullable=False)
    usuario_publicador_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    fecha_hora_publicacion = Column(DateTime, default=datetime.datetime.utcnow)
    mensaje_id_canal = Column(Integer)
    
    enlace = relationship('Enlace', back_populates='publicaciones')
    publicador = relationship('Usuario', back_populates='publicaciones')
    interacciones = relationship('CalificacionReporte', back_populates='publicacion')

class CalificacionReporte(Base):
    __tablename__ = 'calificaciones_reportes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    publicacion_id = Column(Integer, ForeignKey('publicaciones.id'), nullable=False)
    usuario_calificador_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    tipo = Column(String(50), nullable=False) # 'like', 'dislike', 'report_inap'
    fecha_hora = Column(DateTime, default=datetime.datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('publicacion_id', 'usuario_calificador_id', 'tipo', name='_user_pub_interaction_uc'),)
    
    publicacion = relationship('Publicacion', back_populates='interacciones')
    usuario = relationship('Usuario')

# Configurar DB
db_path = os.path.join(os.path.dirname(__file__), 'database.db')
engine = create_engine(f'sqlite:///{db_path}', connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Insert defaults
    db = SessionLocal()
    defaults = ["Adulto", "Anime", "Películas", "Series", "Estrenos Nuevos", "Documentales"]
    for cat in defaults:
        if not db.query(Categoria).filter_by(nombre_categoria=cat).first():
            db.add(Categoria(nombre_categoria=cat))
    db.commit()
    db.close()

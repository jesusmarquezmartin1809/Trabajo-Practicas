-- =========================
-- BASE DE DATOS
-- =========================
CREATE DATABASE IF NOT EXISTS gestor_practicas;
USE gestor_practicas;

-- =========================
-- USUARIOS
-- =========================
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    contrasena VARCHAR(255) NOT NULL,
    rol ENUM('admin', 'profesor', 'alumno') NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- CICLOS
-- =========================
CREATE TABLE ciclos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    anio_inicio YEAR NOT NULL,
    anio_fin YEAR NOT NULL
);

-- =========================
-- PROFESORES
-- =========================
CREATE TABLE profesores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- =========================
-- ALUMNOS
-- =========================
CREATE TABLE alumnos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    ciclo_id INT,
    telefono VARCHAR(20),
    cv_url VARCHAR(255),
    estado ENUM('pendiente', 'asignado') DEFAULT 'pendiente',
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (ciclo_id) REFERENCES ciclos(id) ON DELETE SET NULL
);

-- =========================
-- PROFESOR - CICLO
-- =========================
CREATE TABLE profesor_ciclo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    profesor_id INT NOT NULL,
    ciclo_id INT NOT NULL,
    UNIQUE (profesor_id, ciclo_id),
    FOREIGN KEY (profesor_id) REFERENCES profesores(id) ON DELETE CASCADE,
    FOREIGN KEY (ciclo_id) REFERENCES ciclos(id) ON DELETE CASCADE
);

-- =========================
-- EMPRESAS
-- =========================
CREATE TABLE empresas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    direccion VARCHAR(255),
    web VARCHAR(150),
    email VARCHAR(150),
    telefono VARCHAR(20)
);

-- =========================
-- RESPONSABLES LEGALES
-- =========================
CREATE TABLE responsables_legales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    dni VARCHAR(20) NOT NULL,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
);

-- =========================
-- TUTORES LABORALES
-- =========================
CREATE TABLE tutores_laborales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    dni VARCHAR(20) NOT NULL,
    telefono VARCHAR(20),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
);

-- =========================
-- PLAZAS
-- =========================
CREATE TABLE plazas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    ciclo_id INT NOT NULL,
    total_plazas INT NOT NULL,
    plazas_ocupadas INT DEFAULT 0,
    CHECK (total_plazas >= 0),
    CHECK (plazas_ocupadas >= 0),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    FOREIGN KEY (ciclo_id) REFERENCES ciclos(id) ON DELETE CASCADE
);

-- =========================
-- ASIGNACIONES
-- =========================
CREATE TABLE asignaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alumno_id INT NOT NULL,
    plaza_id INT NOT NULL,
    tutor_laboral_id INT,
    estado ENUM('pendiente', 'confirmada') DEFAULT 'pendiente',
    fecha_asignacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (alumno_id),

    FOREIGN KEY (alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE,
    FOREIGN KEY (plaza_id) REFERENCES plazas(id) ON DELETE CASCADE,
    FOREIGN KEY (tutor_laboral_id) REFERENCES tutores_laborales(id) ON DELETE SET NULL
);

-- =========================
-- SEGUIMIENTO EMPRESAS
-- =========================
CREATE TABLE seguimiento_empresas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    profesor_id INT NOT NULL,
    fecha_hora DATETIME NOT NULL,
    comentario TEXT,

    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    FOREIGN KEY (profesor_id) REFERENCES profesores(id) ON DELETE CASCADE
);

-- =========================
-- CONFIGURACIÓN GLOBAL
-- =========================
CREATE TABLE configuracion_global (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha_inicio_asignacion DATE,
    fecha_fin_asignacion DATE
);

-- =========================
-- IMPORTACIONES CSV
-- =========================
CREATE TABLE importaciones_csv (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo ENUM('alumnos', 'empresas') NOT NULL,
    archivo VARCHAR(255),
    estado ENUM('procesado', 'error') DEFAULT 'procesado',
    errores TEXT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

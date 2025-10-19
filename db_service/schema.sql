CREATE TABLE IF NOT EXISTS student (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    grade VARCHAR(10) NOT NULL,
    UNIQUE KEY unique_student (name, grade)
);

CREATE TABLE IF NOT EXISTS subject (
    subject_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    UNIQUE KEY unique_subject (name, category)
);

CREATE TABLE IF NOT EXISTS field (
    field_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    UNIQUE KEY(name, category)
);

CREATE TABLE IF NOT EXISTS record (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    field_id INT NOT NULL,
    keyword TEXT NOT NULL,
    date DATE NOT NULL,
    ts DATETIME NOT NULL,
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (subject_id) REFERENCES subject(subject_id),
    FOREIGN KEY (field_id) REFERENCES field(field_id)
);



# student_id 저장
INSERT INTO student (name, grade) VALUES ('홍길동', '중2');

# 생기부 종류-과목/반
INSERT INTO subject (name, category) VALUES ('2-8', '행동특성및종합의견');

# 생기부 종류-필드
INSERT INTO field (name, category) VALUES ('책임감', '행동특성및종합의견');

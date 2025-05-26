\! chcp 1251

create database ads_bot encoding 'UTF8';

\c ads_bot

CREATE TABLE Users (
    chat_id BIGINT PRIMARY KEY,
    username VARCHAR(64)
);

CREATE TABLE Category (
    category_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE Record (
    record_id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    category_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    price NUMERIC(10, 2),
    tags TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_user
        FOREIGN KEY (chat_id) 
        REFERENCES Users(chat_id)
        ON DELETE CASCADE,
        
    CONSTRAINT fk_category
        FOREIGN KEY (category_id) 
        REFERENCES Category(category_id)
        ON DELETE RESTRICT
);

CREATE TABLE Photos (
    id SERIAL PRIMARY KEY,
    file_id TEXT NOT NULL,
    file_unique_id TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_record
        FOREIGN KEY (record_id) 
        REFERENCES Record(record_id)
        ON DELETE CASCADE
);

CREATE INDEX idx_record_tags ON Record USING GIN(tags);

CREATE INDEX idx_record_active ON Record(is_active) WHERE is_active = TRUE;

CREATE INDEX idx_record_category ON Record(category_id);
CREATE INDEX idx_record_user ON Record(chat_id);

INSERT INTO Category (name) VALUES 
('Одежда'), ('Книги'), ('Электроника'), 
('Мебель'), ('Бытовая техника'), ('Косметика'),
('Еда'), ('Канцелярия'), ('Другое');

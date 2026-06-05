CREATE TABLE if not exists path (
    path_id SERIAL PRIMARY KEY,
    path_name TEXT NOT NULL,
    parent_id INT REFERENCES path(path_id),
    constraint unique_path_name_parent_id
        unique (path_name, parent_id)
);

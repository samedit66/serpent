class
    APPLICATION

inherit
    WEB_SERVER

create
    make
    
feature
-- Настройка сервера: задания порта и обработчика GET-запросов.

    port: INTEGER = 8000

    get (route: STRING): STRING
    do
        -- route contains the full path and query, e.g. "/test", "/foo?x=1"
        if route = "/test" then
            Result := "<html><body><h1>Hello /test</h1><p>Path: " + route + "</p></body></html>"
        else
            Result := "<html><body><h1>Generic</h1><p>Path: " + route + "</p></body></html>"
        end
    end

feature
-- Запуск сервера.

    make
    do
        run

        io.put_string ("Press ENTER to stop the server...%N")
        io.read_line
        
        stop
    end

end

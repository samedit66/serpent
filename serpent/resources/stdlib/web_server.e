deferred class
    WEB_SERVER
-- Простой веб-сервер с возможностью обрабатывать лишь get-запросы.

feature -- Deferred configuration (must be provided by descendant)

    port: INTEGER
    deferred
    end
    -- Port to listen on (ex: 8000)

    get (route: STRING): STRING
    -- Return HTML body for the given route (a_route is e.g. "/test" or the request path).
    deferred
    end

feature -- Control

    run
    -- Register this Eiffel instance as the HTTP handler and start Java HttpServer.
    local
        ok: INTEGER
    do
        -- register Eiffel object as delegate
        set_java_delegate (Current)
        -- start server on `port` (context is ignored; Java bridge uses "/")
        ok := webserver_start (port, "/")
        if ok = 0 then
            io.put_string ("WEB_SERVER: failed to start server%N")
        else
            io.put_string ("WEB_SERVER: server started on port " + port.out + "%N")
        end
    end

    stop
    -- Stop the Java server and clear delegate
    do
        webserver_stop
        clear_java_delegate
    end

feature {NONE} -- Java externals (bridge to the Java helper jar)

    set_java_delegate (del: ANY)
    -- Set Eiffel object as delegate inside Java MyEiffelHandler.
    external "java"
    alias "com.eiffel.PLATFORM.setDelegate"
    end

    clear_java_delegate
    external "java"
    alias "com.eiffel.PLATFORM.clearDelegate"
    end

    webserver_start (a_port: INTEGER; route: STRING): INTEGER
    external "java"
    alias "com.eiffel.PLATFORM.startServer"
    end

    webserver_stop: INTEGER
    external "java"
    alias "com.eiffel.PLATFORM.stopServer"
    end

end

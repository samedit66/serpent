class
    APPLICATION

create
    make
    
feature
                    
    make
    local
        table: HASH_TABLE [INTEGER; CHARACTER]
        letters: ARRAY [CHARACTER]
        i: INTEGER
    do
        create table.empty

        print ("Введите строчку: ")
        io.read_line
        
        from
            i := 1
        until
            i > io.last_line.count
        loop
            if not table.has_key (io.last_line [i]) then
                table [io.last_line [i]] := 0
            end

            table [io.last_line [i]] := table [io.last_line [i]] + 1
            i := i + 1
        end

        letters := table.current_keys
        from
            i := letters.lower
        until
            i > letters.upper
        loop
            print ("Символ " + letters [i].out + " встречается " + table [letters [i]].out + " раз(а)%N")
            i := i + 1
        end
    end

end

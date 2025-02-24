class INTEGER
inherit ANY
    redefine out end
feature
    out: STRING do print (10) end
feature
    plus (other: like Current): like Current do end
feature
    test
    local
        x: STRING
        y: INTEGER
        z: BASE
    do
        x := ""
        z := create {BASE}
    end
end

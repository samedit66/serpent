class
    APPLICATION

inherit
    IO

create
    make

feature
    make
    local
        tester: ACCESS_B
        a_object: ACCESS_A
    do
        create tester.make
        tester.test_access

        create a_object.make
        -- Ошибочная строчка с некорректным доступом
        println (a_object.secret_value)
    end
end


class
    ACCESS_A

create
    make

feature
    make do end

feature

    public_value: INTEGER
        do
            Result := 10
        end

feature {ACCESS_B}

    secret_value: INTEGER
        do
            Result := 42
        end
end

class PARENT_B
inherit IO
create make
feature
    make do end
    
    test_access_
    local
        a: ACCESS_A
    do
        create a.make
        print ("ACCESS_A public_value: " + a.public_value.out + "%N")
        print ("ACCESS_A secret_value (доступен для ACCESS_B): " + a.secret_value.out + "%N")
    end
end

class
    ACCESS_B

inherit
    IO
    PARENT_B redefine make end

create
    make

feature
    make do end

feature

    test_access
    local
        a: ACCESS_A
    do
        create a.make
        print ("ACCESS_A public_value: " + a.public_value.out + "%N")
        print ("ACCESS_A secret_value (доступен для ACCESS_B): " + a.secret_value.out + "%N")
    end
end

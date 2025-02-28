public class Test {
    int foo() { return 1; }   // OK
    double foo() { return 1.0; }  // Ошибка: конфликт сигнатур в JVM
}
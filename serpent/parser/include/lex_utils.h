#ifndef __LEX_UTILS__
#define __LEX_UTILS__

#include <stdbool.h>
#include "strlist.h"

/**
 * Удаляет знаки нижнего подчеркивания из строки.
 * Используется для очищение литералов целых чисел (записанных
 * в любой системе счисления)
 * 
 * @param str_num строковая запись числа
 */
void
remove_underscores(char *str_num);

/**
 * Конвертирует строку, в которой записан литерал целого числа, в целое число.
 * 
 * @param str_num строковая запись числа
 * @param int_num указатель на переменную, в которую будет записан результат
 * @param base система счисления, в которой записано число
 * (поддерживается двоичная (2), восьмиричная (8), десятичная (10) и
 * шестнадцатиричная (16))
 */
void
parse_int(char *str_num, int *int_num, int base);

/**
 * Конвертирует строку, в которой записан литерал действительного числа, в
 * действительное число
 * 
 * @param str_num  стрковая запись числа
 * @param real_num указатель на переменную, в которую будет записан результат
 */
void
parse_real(char *str_num, double *real_num);

/**
 * Конвертирует символ, записанный в десятичном коде, в символьный тип.
 * Закодированный символ имеет вид "%/abc/", где a, b, c - десятичные цифры,
 * пример: %/10/ - символ перевода строки.
 * 
 * @param encoded_ch закодированный символ
 * @return декодированный символ
 */
char
convert_decimal_encoded_char(char *encoded_ch);

/**
 * Проверяет, что переданный символ является потенциальным "разделителем" между двумя лексемами.
 * Однако, некоторые лексемы могут быть записаны подряд, без разделителя, например,
 * "a:=10", где все три лексемы записаны без каких-либо разделителей. В данном случае,
 * `is_delim(':')` вернет `true`, ровно как `is_delim('=')`. Однако для чисел или букв данная
 * функция вернет `false`. Потенциальным разделителем также являются различные "пробелы": \t, \n и т. д.
 * 
 * @param ch символ
 * @return признак того, что символ - потенциальный разделитель
 */
bool
is_delim(int ch);

/**
 * Проверяет, что переданный символ является "концом" текста - EOF или '\0'.
 * 
 * @param ch символ
 * @return признак того, что символ - конец текста (EOF или '\0')
 */
bool
is_end(int ch);

/**
 * Проверяет, что переданный символ может быть частью целого числа с заданной системой счисления.
 * 
 * @param ch символ
 * @param base основание системы счисления
 * @return признак того, что символ - потенциальная часть целого числа
 */
bool
is_possible_part_of_integer(int ch, int base);

/**
 * Проверяет, что переданный символ может быть часть действительного числа.
 * 
 * @param ch символ
 * @return признак того, что символ - потенциальная часть действительного числа
 */
bool
is_possible_part_of_real(int ch);

/**
 * Проверяет, что переданый символ является цифрой из восьмиричной системы счисления.
 * 
 * @param ch символ
 * @return признак того, что символ - восьмиричная цифра
 */
bool
is_oct_digit(int ch);

/**
 * Проверяет, что переданый символ является цифрой из двоичной системы счисления.
 * 
 * @param ch символ
 * @return признак того, что символ - двоичная цифра
 */
bool
is_bin_digit(int ch);

/**
 * Экранирует переданную строку.
 * 
 * @param str строка
 * @return экранированная строка
 */
char*
escape(char *str);

/**
 * Выравнивает verbatim-строку, удаляя из нее начальные пробелы.
 * Для большей информации: https://www.eiffel.org/doc/eiffel/ET-_Other_Mechanisms
 * 
 * @param verbatim_str verbatim-строка
 */
void
adjust_unaligned_verbatim_string(const StringList *verbatim_str);


/**
 * Считает длину строки в кодировки utf8.
 * Никаких проверов на валидность строки не производится.
 * 
 * @param utf8_str строка в кодировке utf8
 * @return длина строки в utf8 (количество code-points)
 */
int
strlen_utf8(const char *utf8_str);


#endif

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Payload Splitter - Клиентская часть
Фрагментирует пейлоад на части случайной длины и отправляет их в произвольном порядке
"""

import os
import random
import requests
import json
import time
import argparse
from typing import List, Tuple
from datetime import datetime


class PayloadFragmenter:
    """Класс для фрагментации и отправки пейлоада"""
    
    def __init__(self, target_url: str, min_fragment_size: int = 10, max_fragment_size: int = 100):
        """
        Инициализация фрагментатора
        
        Args:
            target_url: URL целевого сервера
            min_fragment_size: Минимальный размер фрагмента в байтах
            max_fragment_size: Максимальный размер фрагмента в байтах
        """
        self.target_url = target_url
        self.min_fragment_size = min_fragment_size
        self.max_fragment_size = max_fragment_size
        self.fragments = []
        self.session_id = None
        
    def load_payload(self, payload_path: str) -> bytes:
        """
        Загрузка пейлоада из файла
        
        Args:
            payload_path: Путь к файлу с пейлоадом
            
        Returns:
            bytes: Содержимое пейлоада
        """
        if not os.path.exists(payload_path):
            raise FileNotFoundError(f"Файл {payload_path} не найден")
        
        with open(payload_path, 'rb') as f:
            return f.read()
    
    def fragment_payload(self, payload: bytes) -> List[Tuple[int, bytes]]:
        """
        Разбивает пейлоад на фрагменты случайной длины
        
        Args:
            payload: Исходный пейлоад
            
        Returns:
            List[Tuple[int, bytes]]: Список кортежей (индекс, фрагмент)
        """
        fragments = []
        offset = 0
        index = 0
        
        while offset < len(payload):
            # Случайный размер фрагмента
            fragment_size = random.randint(
                self.min_fragment_size,
                min(self.max_fragment_size, len(payload) - offset)
            )
            
            fragment = payload[offset:offset + fragment_size]
            fragments.append((index, fragment))
            
            offset += fragment_size
            index += 1
        
        return fragments
    
    def shuffle_fragments(self, fragments: List[Tuple[int, bytes]]) -> List[Tuple[int, bytes]]:
        """
        Перемешивает фрагменты в случайном порядке
        
        Args:
            fragments: Список фрагментов
            
        Returns:
            List[Tuple[int, bytes]]: Перемешанный список
        """
        shuffled = fragments.copy()
        random.shuffle(shuffled)
        return shuffled
    
    def send_fragments(self, fragments: List[Tuple[int, bytes]], delay: float = 0.1) -> dict:
        """
        Отправляет фрагменты на сервер
        
        Args:
            fragments: Список фрагментов для отправки
            delay: Задержка между отправками (секунды)
            
        Returns:
            dict: Результаты отправки
        """
        # Генерируем уникальный session_id
        self.session_id = f"session_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        
        results = {
            'session_id': self.session_id,
            'total_fragments': len(fragments),
            'sent_fragments': 0,
            'failed_fragments': 0,
            'start_time': datetime.now().isoformat(),
            'fragments_info': []
        }
        
        print(f"[*] Начинаем отправку {len(fragments)} фрагментов (session_id: {self.session_id})")
        
        for idx, (fragment_index, fragment_data) in enumerate(fragments):
            try:
                # Кодируем фрагмент в base64 для безопасной передачи
                import base64
                encoded_data = base64.b64encode(fragment_data).decode('utf-8')
                
                payload_data = {
                    'session_id': self.session_id,
                    'fragment_index': fragment_index,
                    'total_fragments': len(fragments),
                    'data': encoded_data
                }
                
                response = requests.post(
                    f"{self.target_url}/api/fragment",
                    json=payload_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    results['sent_fragments'] += 1
                    print(f"[+] Фрагмент {fragment_index + 1}/{len(fragments)} отправлен успешно")
                else:
                    results['failed_fragments'] += 1
                    print(f"[-] Ошибка отправки фрагмента {fragment_index + 1}: {response.status_code}")
                
                results['fragments_info'].append({
                    'index': fragment_index,
                    'size': len(fragment_data),
                    'status': 'success' if response.status_code == 200 else 'failed',
                    'timestamp': datetime.now().isoformat()
                })
                
                # Задержка между отправками
                if delay > 0 and idx < len(fragments) - 1:
                    time.sleep(delay)
                    
            except Exception as e:
                results['failed_fragments'] += 1
                print(f"[-] Исключение при отправке фрагмента {fragment_index + 1}: {str(e)}")
                results['fragments_info'].append({
                    'index': fragment_index,
                    'size': len(fragment_data),
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        results['end_time'] = datetime.now().isoformat()
        return results
    
    def trigger_assembly(self) -> dict:
        """
        Отправляет команду на сборку пейлоада на сервере
        
        Returns:
            dict: Результат сборки
        """
        if not self.session_id:
            raise ValueError("Session ID не установлен. Сначала отправьте фрагменты.")
        
        print(f"[*] Отправка команды на сборку пейлоада (session_id: {self.session_id})")
        
        try:
            response = requests.post(
                f"{self.target_url}/api/assemble",
                json={'session_id': self.session_id},
                timeout=30
            )
            
            result = response.json()
            print(f"[+] Результат сборки: {result.get('status', 'unknown')}")
            return result
            
        except Exception as e:
            print(f"[-] Ошибка при сборке: {str(e)}")
            return {'status': 'error', 'error': str(e)}


def generate_report(results: dict, output_file: str = None) -> str:
    """
    Генерирует отчёт о результатах тестирования
    
    Args:
        results: Результаты отправки фрагментов
        output_file: Путь к файлу для сохранения отчёта
        
    Returns:
        str: Текст отчёта
    """
    report = f"""
Дата и время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ОБЩАЯ ИНФОРМАЦИЯ:
-----------------
Session ID: {results.get('session_id', 'N/A')}
Всего фрагментов: {results.get('total_fragments', 0)}
Успешно отправлено: {results.get('sent_fragments', 0)}
Ошибок отправки: {results.get('failed_fragments', 0)}

ВРЕМЕННЫЕ ХАРАКТЕРИСТИКИ:
--------------------------
Начало отправки: {results.get('start_time', 'N/A')}
Окончание отправки: {results.get('end_time', 'N/A')}

СТАТИСТИКА ФРАГМЕНТОВ:
----------------------
"""
    
    if results.get('fragments_info'):
        sizes = [f['size'] for f in results['fragments_info']]
        report += f"Минимальный размер: {min(sizes)} байт\n"
        report += f"Максимальный размер: {max(sizes)} байт\n"
        report += f"Средний размер: {sum(sizes) // len(sizes)} байт\n"
        report += f"Общий размер: {sum(sizes)} байт\n\n"
    
    report += "ДЕТАЛИ ФРАГМЕНТОВ:\n"
    report += "------------------\n"
    
    for frag_info in results.get('fragments_info', []):
        report += f"Фрагмент #{frag_info.get('index', 'N/A')}: "
        report += f"{frag_info.get('size', 0)} байт - {frag_info.get('status', 'unknown')}\n"
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"[+] Отчёт сохранён в {output_file}")
    
    return report


def main():
    parser = argparse.ArgumentParser(
        description='Smart Payload Splitter - Фрагментатор пейлоадов для обхода IDS/IPS'
    )
    parser.add_argument('payload', help='Путь к файлу с пейлоадом')
    parser.add_argument('-u', '--url', required=True, help='URL целевого сервера')
    parser.add_argument('-min', '--min-size', type=int, default=10, 
                       help='Минимальный размер фрагмента (по умолчанию: 10)')
    parser.add_argument('-max', '--max-size', type=int, default=100,
                       help='Максимальный размер фрагмента (по умолчанию: 100)')
    parser.add_argument('-d', '--delay', type=float, default=0.1,
                       help='Задержка между отправками в секундах (по умолчанию: 0.1)')
    parser.add_argument('-r', '--report', help='Путь для сохранения отчёта')
    parser.add_argument('--no-shuffle', action='store_true',
                       help='Не перемешивать фрагменты (отправить в исходном порядке)')
    parser.add_argument('--assemble', action='store_true',
                       help='Отправить команду на сборку пейлоада после отправки фрагментов')
    
    args = parser.parse_args()
    
    try:
        # Инициализация фрагментатора
        fragmenter = PayloadFragmenter(
            target_url=args.url,
            min_fragment_size=args.min_size,
            max_fragment_size=args.max_size
        )
        
        # Загрузка пейлоада
        print(f"[*] Загрузка пейлоада из {args.payload}")
        payload = fragmenter.load_payload(args.payload)
        print(f"[+] Пейлоад загружен: {len(payload)} байт")
        
        # Фрагментация
        print(f"[*] Фрагментация пейлоада...")
        fragments = fragmenter.fragment_payload(payload)
        print(f"[+] Пейлоад разбит на {len(fragments)} фрагментов")
        
        # Перемешивание (если не отключено)
        if not args.no_shuffle:
            print(f"[*] Перемешивание фрагментов...")
            fragments = fragmenter.shuffle_fragments(fragments)
            print(f"[+] Фрагменты перемешаны")
        
        # Отправка
        results = fragmenter.send_fragments(fragments, delay=args.delay)
        
        # Сборка (если запрошена)
        if args.assemble:
            assembly_result = fragmenter.trigger_assembly()
            results['assembly'] = assembly_result
        
        # Генерация отчёта
        report_file = args.report or f"report_{fragmenter.session_id}.txt"
        report = generate_report(results, report_file)
        print("\n" + report)
        
        print(f"\n[+] Готово! Отчёт сохранён в {report_file}")
        
    except Exception as e:
        print(f"[-] Критическая ошибка: {str(e)}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Payload Splitter - Серверная часть
Веб-сервер для приёма фрагментов и сборки пейлоада
"""

import os
import json
import base64
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
from collections import defaultdict
import threading
import time

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для тестирования

# Хранилище фрагментов в памяти (session_id -> список фрагментов)
fragments_storage = defaultdict(dict)
fragments_lock = threading.Lock()

# HTML шаблон для страницы сборки
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Payload Splitter - Fragment Assembler</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .status {
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            font-weight: bold;
        }
        .status.waiting {
            background: #fff3cd;
            color: #856404;
        }
        .status.ready {
            background: #d4edda;
            color: #155724;
        }
        .status.error {
            background: #f8d7da;
            color: #721c24;
        }
        .fragment-list {
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            margin: 20px 0;
        }
        .fragment-item {
            padding: 8px;
            margin: 5px 0;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            border-radius: 3px;
        }
        .fragment-item.received {
            border-left-color: #28a745;
        }
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px 5px;
            transition: background 0.3s;
        }
        button:hover {
            background: #5568d3;
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        .payload-preview {
            background: #f8f9fa;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
            font-family: monospace;
            white-space: pre-wrap;
            word-break: break-all;
            max-height: 300px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Smart Payload Splitter - Fragment Assembler</h1>
        
        <div id="status" class="status waiting">
            Ожидание фрагментов...
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value" id="received-count">0</div>
                <div class="stat-label">Получено фрагментов</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="total-count">0</div>
                <div class="stat-label">Всего фрагментов</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="progress">0%</div>
                <div class="stat-label">Прогресс</div>
            </div>
        </div>
        
        <div class="fragment-list" id="fragment-list">
            <p style="text-align: center; color: #999;">Фрагменты появятся здесь после получения...</p>
        </div>
        
        <div style="text-align: center;">
            <button id="assemble-btn" onclick="assemblePayload()" disabled>
                Собрать пейлоад
            </button>
            <button onclick="clearStorage()">Очистить</button>
        </div>
        
        <div id="payload-preview" class="payload-preview" style="display: none;">
            <h3>Собранный пейлоад:</h3>
            <pre id="payload-content"></pre>
        </div>
    </div>

    <script>
        const sessionId = '{{ session_id }}';
        let fragments = {};
        let totalFragments = 0;
        let checkInterval = null;

        // Функция для обновления статуса
        function updateStatus() {
            const received = Object.keys(fragments).length;
            const statusDiv = document.getElementById('status');
            const receivedCount = document.getElementById('received-count');
            const totalCount = document.getElementById('total-count');
            const progress = document.getElementById('progress');
            const assembleBtn = document.getElementById('assemble-btn');
            const fragmentList = document.getElementById('fragment-list');

            receivedCount.textContent = received;
            totalCount.textContent = totalFragments;
            
            if (totalFragments > 0) {
                const progressPercent = Math.round((received / totalFragments) * 100);
                progress.textContent = progressPercent + '%';
            }

            if (received === 0) {
                statusDiv.className = 'status waiting';
                statusDiv.textContent = 'Ожидание фрагментов...';
                assembleBtn.disabled = true;
            } else if (received < totalFragments) {
                statusDiv.className = 'status waiting';
                statusDiv.textContent = `Получено ${received} из ${totalFragments} фрагментов...`;
                assembleBtn.disabled = true;
            } else {
                statusDiv.className = 'status ready';
                statusDiv.textContent = 'Все фрагменты получены! Готово к сборке.';
                assembleBtn.disabled = false;
            }

            // Обновление списка фрагментов
            if (received > 0) {
                fragmentList.innerHTML = '';
                for (let i = 0; i < totalFragments; i++) {
                    const fragDiv = document.createElement('div');
                    fragDiv.className = 'fragment-item' + (fragments[i] ? ' received' : '');
                    fragDiv.textContent = `Фрагмент #${i} ${fragments[i] ? '✓ Получен' : '⏳ Ожидание...'}`;
                    fragmentList.appendChild(fragDiv);
                }
            }
        }

        // Функция для получения фрагментов с сервера
        async function fetchFragments() {
            try {
                const response = await fetch(`/api/fragments/${sessionId}`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.fragments) {
                        fragments = data.fragments;
                        totalFragments = data.total_fragments || Object.keys(fragments).length;
                        updateStatus();
                    }
                }
            } catch (error) {
                console.error('Ошибка при получении фрагментов:', error);
            }
        }

        // Функция сборки пейлоада
        async function assemblePayload() {
            try {
                const response = await fetch('/api/assemble', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ session_id: sessionId })
                });

                const result = await response.json();
                
                if (result.status === 'success') {
                    const statusDiv = document.getElementById('status');
                    statusDiv.className = 'status ready';
                    statusDiv.textContent = 'Пейлоад успешно собран!';
                    
                    // Показываем превью пейлоада
                    const previewDiv = document.getElementById('payload-preview');
                    const contentDiv = document.getElementById('payload-content');
                    previewDiv.style.display = 'block';
                    
                    // Показываем первые 500 символов пейлоада
                    const payload = result.payload || '';
                    contentDiv.textContent = payload.substring(0, 500) + 
                        (payload.length > 500 ? '\n\n... (обрезано для отображения)' : '');
                } else {
                    const statusDiv = document.getElementById('status');
                    statusDiv.className = 'status error';
                    statusDiv.textContent = 'Ошибка сборки: ' + (result.error || 'Неизвестная ошибка');
                }
            } catch (error) {
                const statusDiv = document.getElementById('status');
                statusDiv.className = 'status error';
                statusDiv.textContent = 'Ошибка: ' + error.message;
            }
        }

        // Функция очистки
        function clearStorage() {
            fragments = {};
            totalFragments = 0;
            updateStatus();
            document.getElementById('payload-preview').style.display = 'none';
        }

        // Периодическая проверка новых фрагментов
        if (sessionId && sessionId !== '') {
            checkInterval = setInterval(fetchFragments, 1000);
            fetchFragments(); // Первая проверка сразу
        }

        // Очистка интервала при закрытии страницы
        window.addEventListener('beforeunload', () => {
            if (checkInterval) {
                clearInterval(checkInterval);
            }
        });
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Главная страница"""
    return render_template_string(HTML_TEMPLATE, session_id='')


@app.route('/session/<session_id>')
def session_page(session_id):
    """Страница для конкретной сессии"""
    return render_template_string(HTML_TEMPLATE, session_id=session_id)


@app.route('/api/fragment', methods=['POST'])
def receive_fragment():
    """Приём фрагмента от клиента"""
    try:
        data = request.json
        
        session_id = data.get('session_id')
        fragment_index = data.get('fragment_index')
        total_fragments = data.get('total_fragments')
        encoded_data = data.get('data')
        
        if not all([session_id, fragment_index is not None, encoded_data]):
            return jsonify({
                'status': 'error',
                'error': 'Недостаточно данных'
            }), 400
        
        # Декодируем данные
        fragment_data = base64.b64decode(encoded_data)
        
        # Сохраняем фрагмент в памяти
        with fragments_lock:
            if session_id not in fragments_storage:
                fragments_storage[session_id] = {
                    'fragments': {},
                    'total_fragments': total_fragments,
                    'created_at': datetime.now().isoformat()
                }
            
            fragments_storage[session_id]['fragments'][fragment_index] = fragment_data
            fragments_storage[session_id]['last_update'] = datetime.now().isoformat()
        
        return jsonify({
            'status': 'success',
            'message': f'Фрагмент {fragment_index} получен',
            'received_fragments': len(fragments_storage[session_id]['fragments']),
            'total_fragments': total_fragments
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/fragments/<session_id>', methods=['GET'])
def get_fragments(session_id):
    """Получение информации о фрагментах для конкретной сессии"""
    with fragments_lock:
        if session_id not in fragments_storage:
            return jsonify({
                'status': 'not_found',
                'fragments': {},
                'total_fragments': 0
            })
        
        session_data = fragments_storage[session_id]
        # Возвращаем только индексы (без данных для безопасности)
        fragment_indices = list(session_data['fragments'].keys())
        
        return jsonify({
            'status': 'success',
            'fragments': {str(k): True for k in fragment_indices},
            'total_fragments': session_data.get('total_fragments', len(fragment_indices)),
            'received_count': len(fragment_indices)
        })


@app.route('/api/assemble', methods=['POST'])
def assemble_payload():
    """Сборка пейлоада из фрагментов"""
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({
                'status': 'error',
                'error': 'Session ID не указан'
            }), 400
        
        with fragments_lock:
            if session_id not in fragments_storage:
                return jsonify({
                    'status': 'error',
                    'error': 'Сессия не найдена'
                }), 404
            
            session_data = fragments_storage[session_id]
            fragments = session_data['fragments']
            total_fragments = session_data.get('total_fragments', len(fragments))
            
            # Проверяем, все ли фрагменты получены
            if len(fragments) < total_fragments:
                return jsonify({
                    'status': 'error',
                    'error': f'Не все фрагменты получены ({len(fragments)}/{total_fragments})'
                }), 400
            
            # Собираем пейлоад в правильном порядке
            assembled_payload = b''
            for i in range(total_fragments):
                if i not in fragments:
                    return jsonify({
                        'status': 'error',
                        'error': f'Отсутствует фрагмент {i}'
                    }), 400
                assembled_payload += fragments[i]
            
            # Конвертируем в строку для демонстрации (в реальной атаке здесь был бы execution)
            payload_str = assembled_payload.decode('utf-8', errors='replace')
            
            # ВНИМАНИЕ: В реальной атаке здесь был бы код выполнения пейлоада
            # Для демонстрации мы только возвращаем информацию о собранном пейлоаде
            print(f"[!] Пейлоад собран для сессии {session_id}: {len(assembled_payload)} байт")
            print(f"[!] ПРЕДУПРЕЖДЕНИЕ: В реальной атаке здесь был бы execution пейлоада!")
            
            return jsonify({
                'status': 'success',
                'message': 'Пейлоад успешно собран',
                'payload_size': len(assembled_payload),
                'payload': payload_str[:1000],  # Первые 1000 символов для демонстрации
                'assembled_at': datetime.now().isoformat()
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Получение статистики сервера"""
    with fragments_lock:
        active_sessions = len(fragments_storage)
        total_fragments = sum(
            len(session_data['fragments']) 
            for session_data in fragments_storage.values()
        )
        
        return jsonify({
            'active_sessions': active_sessions,
            'total_fragments_stored': total_fragments,
            'sessions': {
                session_id: {
                    'fragments_count': len(session_data['fragments']),
                    'total_fragments': session_data.get('total_fragments', 0),
                    'created_at': session_data.get('created_at'),
                    'last_update': session_data.get('last_update')
                }
                for session_id, session_data in fragments_storage.items()
            }
        })


if __name__ == '__main__':
    print("""
    Сервер запущен на http://localhost:5000
    API endpoints:
      POST /api/fragment - приём фрагмента
      GET  /api/fragments/<session_id> - получение информации о фрагментах
      POST /api/assemble - сборка пейлоада
      GET  /api/stats - статистика сервера
    """)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

import flet as ft
import time
import requests
import threading
import json
import os

# --- إعدادات الحماية: يقرأ الساروت من السيستم (GitHub Secrets) أولاً، وإيلا مالقاهش يستعمل الافتراضي ---
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "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")

NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL_NAME = "meta/llama-3.1-8b-instruct" 

HISTORY_FILE = "chat_history.json"
PROFILE_FILE = "user_profile.json"

def main(page: ft.Page):
    page.title = "NIBRAS AI"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#090D16" 
    
    # تثبيت الحجم على شكل هاتف ذكي
    page.window_width = 390
    page.window_height = 740
    page.window_max_width = 390
    page.window_max_height = 740
    page.window_resizable = False  
    page.padding = 0 

    user_data = {"name": "", "birthdate": "", "level": ""}

    # --- دوال الـ JSON ---
    def is_user_registered():
        if os.path.exists(PROFILE_FILE):
            try:
                with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    user_data["name"] = data.get("name", "")
                    user_data["birthdate"] = data.get("birthdate", "")
                    user_data["level"] = data.get("level", "")
                return True
            except:
                return False
        return False

    def save_user_profile(name, birthdate, level):
        data = {"name": name, "birthdate": birthdate, "level": level}
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_chats_from_json():
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        else:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
            return []

    def save_chat_to_json(user_msg, ai_reply):
        chats = load_chats_from_json()
        chats.append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M"),
            "user": user_msg,
            "ai": ai_reply
        })
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(chats, f, ensure_ascii=False, indent=4)

    # ----------------------------------------------------
    # 1. شاشة الـ Splash Screen
    # ----------------------------------------------------
    def splash_timeout():
        if is_user_registered():
            time.sleep(1.0)
            show_chat()
        else:
            time.sleep(1.5)
            show_onboarding()

    def show_splash():
        page.clean()
        splash_title = ft.Text("NIBRAS AI", size=45, weight=ft.FontWeight.BOLD, color="#00E5FF")
        splash_sub = ft.Text("powered by IBAN", size=14, color="#64748B")
        loader = ft.ProgressRing(width=28, height=28, stroke_width=3, color="#00E5FF")
        version_text = ft.Text("V 1.0 Beta", size=12, color="#334155", weight=ft.FontWeight.W_500)
        
        page.add(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Container(expand=True),
                        ft.Column([splash_title, splash_sub, ft.Container(height=40), loader], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Container(expand=True),
                        ft.Container(content=version_text, margin=ft.margin.only(bottom=20))
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                expand=True
            )
        )
        page.update()
        threading.Thread(target=splash_timeout).start()

    # ----------------------------------------------------
    # 2. شاشة الـ Onboarding (مع إضافة سكرول مرن)
    # ----------------------------------------------------
    def onboarding_timeout():
        time.sleep(2.5) 
        show_chat()

    def show_onboarding():
        page.clean()
        
        title = ft.Text("Welcome to NIBRAS", size=28, weight=ft.FontWeight.BOLD, color="white")
        desc = ft.Text("Please fill your information to continue", size=14, color="#64748B")
        
        name_input = ft.TextField(label="Full Name", border_color="#1E293B", focused_border_color="#00E5FF", bgcolor="#111827", color="white", filled=True, border_radius=10)
        birth_input = ft.TextField(label="Birthdate (DD/MM/YYYY)", border_color="#1E293B", focused_border_color="#00E5FF", bgcolor="#111827", color="white", filled=True, border_radius=10)
        level_input = ft.TextField(label="Educational Level", border_color="#1E293B", focused_border_color="#00E5FF", bgcolor="#111827", color="white", filled=True, border_radius=10)
        
        def on_done_click(e):
            if name_input.value and birth_input.value and level_input.value:
                save_user_profile(name_input.value, birth_input.value, level_input.value)
                user_data["name"] = name_input.value
                user_data["birthdate"] = birth_input.value
                user_data["level"] = level_input.value
                
                load_chats_from_json()

                page.clean()
                loading_text = ft.Text("Setting up your AI environment...", size=16, color="#00E5FF")
                loader = ft.ProgressBar(width=250, color="#00E5FF", bgcolor="#1E293B")
                
                page.add(
                    ft.Container(
                        content=ft.Column([loading_text, ft.Container(height=15), loader], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                        expand=True
                    )
                )
                page.update()
                threading.Thread(target=onboarding_timeout).start()
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Please fill all fields!"), open=True)
                page.update()

        done_btn = ft.ElevatedButton(
            content=ft.Text("DONE", color="#090D16", weight=ft.FontWeight.BOLD),
            bgcolor="#00E5FF", width=200, height=45, on_click=on_done_click
        )
        
        page.add(
            ft.Container(
                content=ft.Column(
                    controls=[title, desc, ft.Container(height=20), name_input, ft.Container(height=10), birth_input, ft.Container(height=10), level_input, ft.Container(height=30), done_btn],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.AUTO # سكرول آمن ف حالة صغرت الشاشة بسبب الكيبورد
                ),
                padding=25, expand=True
            )
        )
        page.update()

    # ----------------------------------------------------
    # 3. الشاشة الرئيسية د الشات
    # ----------------------------------------------------
    def show_chat():
        page.clean()
        
        chat_history = ft.ListView(expand=True, spacing=14, auto_scroll=True, padding=10)
        
        display_name = user_data["name"] if user_data["name"] else "Ibrahim"
        
        welcome_box = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(f"Hello {display_name}, ", size=20, weight=ft.FontWeight.W_600, color="#00E5FF"),
                            ft.Text("I am NIBRAS", size=20, weight=ft.FontWeight.W_600, color="#C084FC")
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    ft.Text("Your premium AI concierge.", size=13, color="#CBD5E1")
                ],
                spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            alignment=ft.Alignment(0, 0), padding=20,
            bgcolor="#111827", border_radius=20
        )
        chat_history.controls.append(welcome_box)

        chat_input = ft.TextField(
            hint_text="Ask NIBRAS anything...",
            expand=True, 
            multiline=True, 
            min_lines=1, 
            max_lines=3,
            border=ft.InputBorder.OUTLINE,
            border_radius=25,
            border_color="#1E293B",
            focused_border_color="#00E5FF", 
            bgcolor="#111827", 
            cursor_color="#00E5FF",
            color="white",
            content_padding=ft.padding.symmetric(vertical=10, horizontal=18),
            shift_enter=True
        )

        def load_selected_chat(user_msg, ai_reply):
            chat_history.controls.clear()
            
            user_bubble = ft.Container(
                content=ft.Text(user_msg, color="white", size=15),
                bgcolor="#00E5FF15", padding=14, border_radius=18,
                border=ft.border.all(1, "#00E5FF30")
            )
            ai_bubble = ft.Container(
                content=ft.Text(ai_reply, color="#E2E8F0", size=15),
                bgcolor="#111827", padding=14, border_radius=18,
                width=280
            )
            
            chat_history.controls.append(ft.Row(controls=[user_bubble], alignment=ft.MainAxisAlignment.END))
            chat_history.controls.append(ft.Row(controls=[ai_bubble], alignment=ft.MainAxisAlignment.START))
            
            sidebar.open = False
            page.update()

        def start_new_chat(e):
            chat_history.controls.clear()
            chat_history.controls.append(welcome_box)
            sidebar.open = False
            page.update()

        sidebar = ft.NavigationDrawer(
            bgcolor="#0A0F1D",
            controls=[]
        )
        page.drawer = sidebar 

        def update_sidebar_history():
            sidebar.controls = [
                ft.Container(
                    content=ft.Text("Saved Chats", size=18, weight=ft.FontWeight.BOLD, color="#00E5FF"),
                    padding=ft.padding.only(left=20, top=22, right=20, bottom=14)
                ),
                ft.NavigationDrawerDestination(
                    icon=ft.Icons.ADD_ROUNDED,
                    label="New Chat"
                ),
                ft.Container(height=1, bgcolor="#1E293B"),
                ft.Container(content=ft.Text("Recent chat history", color="#94A3B8", size=12), padding=ft.padding.only(left=20, top=10, right=20, bottom=10))
            ]
            
            saved_chats = load_chats_from_json()
            if not saved_chats:
                sidebar.controls.append(ft.Container(content=ft.Text("No chats saved yet.", color="#94A3B8"), padding=20))
            else:
                for c in reversed(saved_chats):
                    u_msg = c['user']
                    sidebar.controls.append(
                        ft.NavigationDrawerDestination(
                            icon=ft.Icons.CHAT_BUBBLE_OUTLINE,
                            label=f"{u_msg[:18]}..."
                        )
                    )
            
            def on_sidebar_change(e):
                idx = int(sidebar.selected_index)
                if idx == 1:
                    start_new_chat(None)
                    return
                
                index_in_list = idx - 4 
                saved = list(reversed(load_chats_from_json()))
                if 0 <= index_in_list < len(saved):
                    load_selected_chat(saved[index_in_list]['user'], saved[index_in_list]['ai'])

            sidebar.on_change = on_sidebar_change
            page.update()

        def open_drawer(e):
            update_sidebar_history()
            sidebar.open = True
            page.update()

        menu_button = ft.IconButton(
            icon=ft.Icons.MENU_ROUNDED,
            icon_color="#00E5FF",
            icon_size=28,
            on_click=open_drawer
        )

        page.appbar = ft.AppBar(
            leading=menu_button,
            title=ft.Text("NIBRAS AI", color="white", weight=ft.FontWeight.BOLD, size=18),
            center_title=True,
            bgcolor="#0A0F1D",
            elevation=0
        )

        def send_message(e):
            user_msg = chat_input.value.strip()
            if not user_msg:
                return
            
            if welcome_box in chat_history.controls:
                chat_history.controls.remove(welcome_box)
            
            user_bubble = ft.Container(
                content=ft.Text(user_msg, color="white", size=15),
                bgcolor="#00E5FF15", padding=14, border_radius=18,
                border=ft.border.all(1, "#00E5FF30")
            )
            chat_history.controls.append(ft.Row(controls=[user_bubble], alignment=ft.MainAxisAlignment.END))
            chat_input.value = ""
            
            thinking_bubble = ft.Container(
                content=ft.Row([
                    ft.ProgressRing(width=12, height=12, stroke_width=2, color="#00E5FF"),
                    ft.Text(" NIBRAS is writing...", size=14, color="#E2E8F0")
                ], spacing=10),
                bgcolor="#111827", padding=14, border_radius=18,
                width=200
            )
            thinking_row = ft.Row(controls=[thinking_bubble], alignment=ft.MainAxisAlignment.START)
            chat_history.controls.append(thinking_row)
            page.update()

            def get_gemini_response():
                headers = {
                    "Authorization": f"Bearer {NVIDIA_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": MODEL_NAME,
                    "messages": [
                        {
                            "role": "system", 
                            "content": "You are a helpful and natural AI assistant named NIBRAS AI. Only if the user explicitly asks about your identity, name, or creator, mention that you are NIBRAS AI developed by Ibrahim Anwar (إبراهيم أنور). Otherwise, just chat normally and naturally without repeating your identity or creator name."
                        },
                        {"role": "user", "content": user_msg}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1024
                }

                try:
                    response = requests.post(NVIDIA_URL, headers=headers, json=payload, timeout=15)
                    if response.status_code == 200:
                        res_data = response.json()
                        ai_reply = res_data['choices'][0]['message']['content']
                        save_chat_to_json(user_msg, ai_reply)
                    else:
                        ai_reply = f"خطأ من NVIDIA API: {response.status_code}\nتأكد أن الساروت والموديل صحاح."
                except Exception as ex:
                    ai_reply = f"مشكل ف الاتصال: {str(ex)}"

                chat_history.controls.remove(thinking_row)
                
                ai_bubble = ft.Container(
                    content=ft.Text(ai_reply, color="#E2E8F0", size=15),
                    bgcolor="#111827", padding=14, border_radius=18,
                    width=280
                )
                chat_history.controls.append(ft.Row(controls=[ai_bubble], alignment=ft.MainAxisAlignment.START))
                page.update()

            threading.Thread(target=get_gemini_response, daemon=True).start()

        send_btn = ft.IconButton(
            icon=ft.Icons.SEND_ROUNDED,
            icon_color="#00E5FF",
            icon_size=26,
            on_click=send_message
        )

        input_row = ft.Row(
            controls=[chat_input, send_btn], 
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER
        )

        main_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=chat_history, expand=True, padding=0,
                        bgcolor="#0A0F1D"
                    ),
                    ft.Divider(color="#1E293B", height=1),
                    ft.Container(
                        content=input_row, padding=ft.padding.only(left=5, right=5, top=5, bottom=15), bgcolor="#090D16"
                    )
                ],
                spacing=5, expand=True
            ),
            expand=True, bgcolor="#090D16"
        )

        page.add(main_container)
        page.update()

    show_splash()

ft.app(target=main)
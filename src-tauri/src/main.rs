#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{Manager, SystemTray, SystemTrayMenu, SystemTrayMenuItem, CustomMenuItem};
use std::process::{Command, Child};
use std::sync::Mutex;

struct EngineProcess(Mutex<Option<Child>>);

#[tauri::command]
fn start_engine() -> Result<String, String> {
    Ok("Engine started via uvicorn".to_string())
}

#[tauri::command]
fn open_url(url: String) -> Result<(), String> {
    open::that(&url).map_err(|e| e.to_string())
}

fn main() {
    // System tray
    let quit    = CustomMenuItem::new("quit",  "Quit AppDrop");
    let show    = CustomMenuItem::new("show",  "Show Window");
    let engine  = CustomMenuItem::new("engine","Restart Engine");
    let tray_menu = SystemTrayMenu::new()
        .add_item(show)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(engine)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(quit);
    let tray = SystemTray::new().with_menu(tray_menu);

    tauri::Builder::default()
        .system_tray(tray)
        .manage(EngineProcess(Mutex::new(None)))
        .on_system_tray_event(|app, event| match event {
            tauri::SystemTrayEvent::MenuItemClick { id, .. } => match id.as_str() {
                "quit"   => std::process::exit(0),
                "show"   => { let w = app.get_window("main").unwrap(); w.show().unwrap(); },
                "engine" => { /* TODO: restart engine */ }
                _ => {}
            },
            _ => {}
        })
        .setup(|app| {
            // Auto-start Python engine on app launch
            let _child = Command::new("python3")
                .args(["-m","uvicorn","main:app","--host","127.0.0.1","--port","8742","--log-level","error"])
                .current_dir(app.path_resolver().app_dir().unwrap().join("engine"))
                .spawn();
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![start_engine, open_url])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

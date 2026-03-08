#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{Manager, SystemTray, SystemTrayMenu, SystemTrayMenuItem, CustomMenuItem};
use std::process::{Command, Child};
use std::sync::Mutex;
use std::path::PathBuf;

struct EngineProcess(Mutex<Option<Child>>);

#[tauri::command]
fn start_engine() -> Result<String, String> {
    Ok("Engine started via uvicorn".to_string())
}

#[tauri::command]
fn open_url(url: String) -> Result<(), String> {
    open::that(&url).map_err(|e| e.to_string())
}

fn engine_dir(app: &tauri::App) -> PathBuf {
    // Primary: engine/ next to the app binary
    let binary_dir = std::env::current_exe()
        .ok()
        .and_then(|p| p.parent().map(|d| d.to_path_buf()));

    if let Some(dir) = binary_dir {
        let candidate = dir.join("engine");
        if candidate.join("main.py").exists() {
            return candidate;
        }
        // macOS .app bundle: binary is in MacOS/, engine is in Resources/engine/
        let resources_candidate = dir.join("../Resources/engine");
        if resources_candidate.join("main.py").exists() {
            return resources_candidate.canonicalize().unwrap_or(resources_candidate);
        }
    }

    // Fallback: app_dir() (installed resources)
    if let Some(dir) = app.path_resolver().app_dir() {
        let candidate = dir.join("engine");
        if candidate.join("main.py").exists() {
            return candidate;
        }
    }

    // Last resort: ~/Downloads/appdrop/engine/
    dirs_next::home_dir()
        .unwrap_or_else(|| PathBuf::from("/"))
        .join("Downloads/appdrop/engine")
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
            let dir = engine_dir(app);
            let _child = Command::new("python3")
                .args(["-m","uvicorn","main:app","--host","127.0.0.1","--port","8742","--log-level","error"])
                .current_dir(&dir)
                .spawn();
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![start_engine, open_url])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#!/usr/bin/env python
import DaVinciResolveScript as dvr

def main():
    resolve = dvr.scriptapp("Resolve")
    if not resolve:
        print("Could not connect to Resolve")
        return

    projectManager = resolve.GetProjectManager()
    project = projectManager.GetCurrentProject()
    
    print("-" * 30)
    print("✅ SUCCESS! Script is running inside Resolve!")
    print(f"🎬 Version: {resolve.GetVersion()}")
    
    if project:
        print(f"📁 Current Project: {project.GetName()}")
        
        # Create a test bin to prove control
        mediaPool = project.GetMediaPool()
        root = mediaPool.GetRootFolder()
        try:
            mediaPool.AddSubFolder(root, "Test_Bin_From_Python")
            print("📂 Created folder 'Test_Bin_From_Python' in Media Pool")
        except:
            print("⚠️ Could not create bin (maybe already exists)")
            
    print("-" * 30)
    print("You can now automate your workflow!")

if __name__ == "__main__":
    main()

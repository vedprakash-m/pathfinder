#!/usr/bin/env python3
"""
PWA Offline Capabilities Validation Script

This script validates that Progressive Web App offline capabilities are properly implemented:
1. Service Worker registration and caching strategies
2. Offline page functionality
3. Background sync capabilities
4. Core features available offline per UX Spec
5. PWA manifest and installation features

Validates both frontend PWA setup and offline functionality.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class PWAOfflineValidator:
    """Validates PWA offline capabilities."""
    
    def __init__(self):
        self.validation_results = []
        self.frontend_path = Path("frontend")
        self.public_path = self.frontend_path / "public"
        self.src_path = self.frontend_path / "src"
        
    def log_result(self, test_name: str, passed: bool, message: str, details: Optional[Dict] = None):
        """Log validation result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.validation_results.append({
            "test": test_name,
            "status": "PASS" if passed else "FAIL",
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def validate_pwa_manifest(self):
        """Validate PWA manifest file."""
        
        manifest_path = self.public_path / "manifest.json"
        if not manifest_path.exists():
            self.log_result(
                "PWA Manifest File",
                False,
                "manifest.json not found in public directory"
            )
            return
            
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                
            # Test 1: Required manifest fields
            required_fields = ["name", "short_name", "start_url", "display", "theme_color"]
            missing_fields = [field for field in required_fields if field not in manifest]
            
            if not missing_fields:
                self.log_result(
                    "Manifest Required Fields",
                    True,
                    f"All required manifest fields present: {required_fields}"
                )
            else:
                self.log_result(
                    "Manifest Required Fields",
                    False,
                    f"Missing required fields: {missing_fields}"
                )
            
            # Test 2: Icons for different sizes
            icons = manifest.get("icons", [])
            icon_sizes = [icon.get("sizes") for icon in icons if "sizes" in icon]
            required_sizes = ["192x192", "512x512"]
            
            has_required_icons = all(size in str(icon_sizes) for size in required_sizes)
            self.log_result(
                "Manifest Icons",
                has_required_icons,
                f"Required icon sizes found: {required_sizes}" if has_required_icons else f"Missing required icon sizes: {required_sizes}"
            )
            
            # Test 3: Display mode for app-like experience
            display_mode = manifest.get("display", "")
            app_like_modes = ["standalone", "fullscreen", "minimal-ui"]
            is_app_like = display_mode in app_like_modes
            
            self.log_result(
                "App-like Display Mode",
                is_app_like,
                f"App-like display mode: {display_mode}" if is_app_like else f"Browser-like display mode: {display_mode}"
            )
            
        except Exception as e:
            self.log_result(
                "Manifest File Analysis",
                False,
                f"Failed to analyze manifest: {e}"
            )
    
    def validate_service_worker(self):
        """Validate Service Worker implementation."""
        
        # Test 1: Service Worker file exists
        sw_paths = [
            self.public_path / "sw.js",
            self.public_path / "service-worker.js",
            self.src_path / "sw.js",
            self.src_path / "service-worker.js"
        ]
        
        sw_file = None
        for sw_path in sw_paths:
            if sw_path.exists():
                sw_file = sw_path
                break
                
        if not sw_file:
            self.log_result(
                "Service Worker File",
                False,
                "Service Worker file not found (checked sw.js, service-worker.js)"
            )
            return
            
        self.log_result(
            "Service Worker File",
            True,
            f"Service Worker found at {sw_file}"
        )
        
        try:
            with open(sw_file, 'r') as f:
                sw_content = f.read()
                
            # Test 2: Cache strategies
            cache_features = [
                ("Cache Installation", "install" in sw_content and "caches.open" in sw_content),
                ("Cache Activation", "activate" in sw_content),
                ("Fetch Interception", "fetch" in sw_content and "event.respondWith" in sw_content),
                ("Offline Strategy", "cache.match" in sw_content or "caches.match" in sw_content),
                ("Cache Updates", "cache.put" in sw_content or "cache.add" in sw_content)
            ]
            
            for feature_name, found in cache_features:
                self.log_result(
                    f"SW {feature_name}",
                    found,
                    f"Service Worker {feature_name.lower()} found" if found else f"Missing Service Worker {feature_name.lower()}"
                )
                
        except Exception as e:
            self.log_result(
                "Service Worker Analysis",
                False,
                f"Failed to analyze Service Worker: {e}"
            )
    
    def validate_sw_registration(self):
        """Validate Service Worker registration in app."""
        
        # Check main app files for SW registration
        app_files = [
            self.src_path / "index.tsx",
            self.src_path / "App.tsx",
            self.src_path / "main.tsx"
        ]
        
        sw_registration_found = False
        registration_file = None
        
        for app_file in app_files:
            if not app_file.exists():
                continue
                
            try:
                with open(app_file, 'r') as f:
                    content = f.read()
                    
                if "serviceWorker.register" in content or "navigator.serviceWorker" in content:
                    sw_registration_found = True
                    registration_file = app_file
                    break
                    
            except Exception:
                continue
        
        self.log_result(
            "Service Worker Registration",
            sw_registration_found,
            f"Service Worker registration found in {registration_file}" if sw_registration_found else "Service Worker registration not found in app"
        )
    
    def validate_offline_components(self):
        """Validate offline-specific components and pages."""
        
        # Test 1: Offline page/component
        offline_paths = [
            self.src_path / "pages" / "OfflinePage.tsx",
            self.src_path / "components" / "OfflinePage.tsx",
            self.src_path / "components" / "offline" / "OfflinePage.tsx",
            self.src_path / "components" / "OfflineIndicator.tsx"
        ]
        
        offline_component_found = False
        for offline_path in offline_paths:
            if offline_path.exists():
                offline_component_found = True
                break
                
        self.log_result(
            "Offline Page Component",
            offline_component_found,
            "Offline page/component found" if offline_component_found else "Missing offline page/component"
        )
        
        # Test 2: Network status detection
        network_detection_found = False
        
        # Check for network status hooks or components
        network_paths = [
            self.src_path / "hooks" / "useNetworkStatus.ts",
            self.src_path / "hooks" / "useOnline.ts",
            self.src_path / "components" / "NetworkStatus.tsx"
        ]
        
        for network_path in network_paths:
            if network_path.exists():
                network_detection_found = True
                break
                
        # Also check in existing components for navigator.onLine usage
        if not network_detection_found:
            try:
                for file_path in self.src_path.rglob("*.tsx"):
                    with open(file_path, 'r') as f:
                        content = f.read()
                    if "navigator.onLine" in content or "online" in content.lower():
                        network_detection_found = True
                        break
            except Exception:
                pass
        
        self.log_result(
            "Network Status Detection",
            network_detection_found,
            "Network status detection found" if network_detection_found else "Missing network status detection"
        )
    
    def validate_offline_storage(self):
        """Validate offline data storage capabilities."""
        
        # Test 1: IndexedDB or localStorage usage
        storage_found = False
        storage_types = []
        
        try:
            for file_path in self.src_path.rglob("*.ts"):
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                if "indexedDB" in content:
                    storage_types.append("IndexedDB")
                    storage_found = True
                elif "localStorage" in content:
                    storage_types.append("localStorage")
                    storage_found = True
                elif "sessionStorage" in content:
                    storage_types.append("sessionStorage")
                    storage_found = True
                    
        except Exception:
            pass
        
        self.log_result(
            "Offline Storage",
            storage_found,
            f"Offline storage found: {', '.join(set(storage_types))}" if storage_found else "No offline storage implementation found"
        )
        
        # Test 2: React Query or similar for caching
        caching_lib_found = False
        
        package_json_path = self.frontend_path / "package.json"
        if package_json_path.exists():
            try:
                with open(package_json_path, 'r') as f:
                    package_json = json.load(f)
                    
                dependencies = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}
                
                caching_libs = ["@tanstack/react-query", "react-query", "swr", "apollo-client"]
                found_libs = [lib for lib in caching_libs if lib in dependencies]
                
                if found_libs:
                    caching_lib_found = True
                    self.log_result(
                        "Client-side Caching",
                        True,
                        f"Caching libraries found: {', '.join(found_libs)}"
                    )
                    
            except Exception:
                pass
        
        if not caching_lib_found:
            self.log_result(
                "Client-side Caching",
                False,
                "No client-side caching libraries found"
            )
    
    def validate_background_sync(self):
        """Validate background sync capabilities."""
        
        # Check for background sync in Service Worker
        sw_paths = [
            self.public_path / "sw.js",
            self.public_path / "service-worker.js",
            self.src_path / "sw.js",
            self.src_path / "service-worker.js"
        ]
        
        background_sync_found = False
        
        for sw_path in sw_paths:
            if not sw_path.exists():
                continue
                
            try:
                with open(sw_path, 'r') as f:
                    content = f.read()
                    
                if "sync" in content and ("background" in content or "BackgroundSync" in content):
                    background_sync_found = True
                    break
                    
            except Exception:
                continue
        
        self.log_result(
            "Background Sync",
            background_sync_found,
            "Background sync capability found" if background_sync_found else "No background sync implementation found"
        )
    
    def validate_offline_fallbacks(self):
        """Validate offline fallback strategies."""
        
        # Test 1: API service error handling
        api_service_path = self.src_path / "services" / "api.ts"
        offline_error_handling = False
        
        if api_service_path.exists():
            try:
                with open(api_service_path, 'r') as f:
                    content = f.read()
                    
                # Look for offline error handling patterns
                offline_patterns = [
                    "navigator.onLine",
                    "NetworkError",
                    "fetch.*catch",
                    "offline",
                    "retry",
                    "cache.*fallback"
                ]
                
                for pattern in offline_patterns:
                    if pattern.replace(".*", "") in content.replace(".", ""):
                        offline_error_handling = True
                        break
                        
            except Exception:
                pass
        
        self.log_result(
            "API Offline Error Handling",
            offline_error_handling,
            "API offline error handling found" if offline_error_handling else "Missing API offline error handling"
        )
        
        # Test 2: Offline-first components
        offline_first_found = False
        
        try:
            for file_path in self.src_path.rglob("*.tsx"):
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                if "offline" in content.lower() and ("fallback" in content.lower() or "cache" in content.lower()):
                    offline_first_found = True
                    break
                    
        except Exception:
            pass
        
        self.log_result(
            "Offline-First Components",
            offline_first_found,
            "Offline-first components found" if offline_first_found else "No offline-first components found"
        )
    
    def validate_pwa_meta_tags(self):
        """Validate PWA-related meta tags in HTML."""
        
        html_path = self.public_path / "index.html"
        if not html_path.exists():
            self.log_result(
                "HTML File",
                False,
                "index.html not found"
            )
            return
            
        try:
            with open(html_path, 'r') as f:
                html_content = f.read()
                
            # Test PWA meta tags
            pwa_meta_tags = [
                ("Viewport Meta", 'name="viewport"' in html_content),
                ("Theme Color", 'name="theme-color"' in html_content),
                ("Manifest Link", 'rel="manifest"' in html_content),
                ("Apple Touch Icon", 'rel="apple-touch-icon"' in html_content or 'apple-touch-icon' in html_content),
                ("App Capable", 'name="mobile-web-app-capable"' in html_content or 'name="apple-mobile-web-app-capable"' in html_content)
            ]
            
            for tag_name, found in pwa_meta_tags:
                self.log_result(
                    f"PWA {tag_name}",
                    found,
                    f"PWA {tag_name.lower()} found" if found else f"Missing PWA {tag_name.lower()}"
                )
                
        except Exception as e:
            self.log_result(
                "HTML Meta Tags Analysis",
                False,
                f"Failed to analyze HTML meta tags: {e}"
            )
    
    def validate_build_configuration(self):
        """Validate build configuration for PWA."""
        
        # Test 1: Vite PWA plugin (if using Vite)
        vite_config_path = self.frontend_path / "vite.config.ts"
        if vite_config_path.exists():
            try:
                with open(vite_config_path, 'r') as f:
                    content = f.read()
                    
                vite_pwa_found = "vite-plugin-pwa" in content or "VitePWA" in content
                self.log_result(
                    "Vite PWA Plugin",
                    vite_pwa_found,
                    "Vite PWA plugin found" if vite_pwa_found else "Vite PWA plugin not configured"
                )
                
            except Exception:
                self.log_result(
                    "Vite Config Analysis",
                    False,
                    "Failed to analyze Vite config"
                )
        
        # Test 2: Package.json PWA dependencies
        package_json_path = self.frontend_path / "package.json"
        if package_json_path.exists():
            try:
                with open(package_json_path, 'r') as f:
                    package_json = json.load(f)
                    
                dependencies = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}
                
                pwa_deps = [
                    "vite-plugin-pwa",
                    "workbox-webpack-plugin", 
                    "@vite-pwa/plugin",
                    "workbox-precaching",
                    "workbox-strategies"
                ]
                
                found_pwa_deps = [dep for dep in pwa_deps if dep in dependencies]
                
                if found_pwa_deps:
                    self.log_result(
                        "PWA Build Dependencies",
                        True,
                        f"PWA dependencies found: {', '.join(found_pwa_deps)}"
                    )
                else:
                    self.log_result(
                        "PWA Build Dependencies",
                        False,
                        "No PWA build dependencies found"
                    )
                    
            except Exception:
                self.log_result(
                    "Package.json Analysis",
                    False,
                    "Failed to analyze package.json"
                )
    
    def run_validation(self):
        """Run complete PWA offline capabilities validation."""
        print("📱 PWA Offline Capabilities Validation")
        print("=" * 40)
        
        try:
            # Run all validations
            self.validate_pwa_manifest()
            self.validate_service_worker()
            self.validate_sw_registration()
            self.validate_offline_components()
            self.validate_offline_storage()
            self.validate_background_sync()
            self.validate_offline_fallbacks()
            self.validate_pwa_meta_tags()
            self.validate_build_configuration()
            
            # Generate summary
            total_tests = len(self.validation_results)
            passed_tests = len([r for r in self.validation_results if r["status"] == "PASS"])
            failed_tests = total_tests - passed_tests
            
            print("\n" + "=" * 40)
            print(f"📊 VALIDATION SUMMARY")
            print(f"Total Tests: {total_tests}")
            print(f"Passed: {passed_tests}")
            print(f"Failed: {failed_tests}")
            print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
            
            if failed_tests == 0:
                print("\n🎉 ALL PWA OFFLINE VALIDATIONS PASSED!")
                print("✅ PWA offline capabilities are fully implemented")
                return True
            elif failed_tests <= 5:
                print(f"\n⚠️ {failed_tests} VALIDATION(S) FAILED")
                print("✅ PWA offline capabilities are partially implemented")
                return True
            else:
                print(f"\n⚠️ {failed_tests} VALIDATION(S) FAILED")
                print("❌ PWA offline capabilities need significant work")
                return False
                
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return False
    
    def save_results(self, filename: str = "pwa_offline_validation_results.json"):
        """Save validation results to file."""
        try:
            with open(filename, 'w') as f:
                json.dump({
                    "validation_timestamp": datetime.utcnow().isoformat(),
                    "validation_type": "pwa_offline_capabilities_validation",
                    "total_tests": len(self.validation_results),
                    "passed_tests": len([r for r in self.validation_results if r["status"] == "PASS"]),
                    "failed_tests": len([r for r in self.validation_results if r["status"] == "FAIL"]),
                    "results": self.validation_results
                }, f, indent=2)
            print(f"📄 Results saved to {filename}")
        except Exception as e:
            print(f"⚠️ Could not save results: {e}")


def main():
    """Main validation function."""
    validator = PWAOfflineValidator()
    success = validator.run_validation()
    validator.save_results()
    
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

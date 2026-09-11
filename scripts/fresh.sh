#!/bin/bash
# Launch a rebadged, zero-content copy of Egg alongside the real one — the
# first-time-user experience on demand. The copy runs as "Egg Fresh"
# (com.feedegg.egg.fresh): its state lives under EGG_DATA_DIR (wiped on every
# run unless --keep), its defaults in the fresh domain, and its Keychain entry
# under the fresh bundle id. The real install's library, settings, credentials,
# and TCC grants are never touched — and macOS will re-prompt for permissions,
# which is part of the first-run experience being rehearsed.
set -euo pipefail

KEEP=0
for arg in "$@"; do
    case "$arg" in
        --keep) KEEP=1 ;;
        *) echo "usage: fresh.sh [--keep]   (--keep retains the fresh profile's data between runs)" >&2
           exit 2 ;;
    esac
done

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_ROOT="$PROJECT_ROOT/DerivedData/Fresh"
APP_PATH="$BUILD_ROOT/Build/Products/Debug/Egg.app"
FRESH_ID="com.feedegg.egg.fresh"
FRESH_APP="$BUILD_ROOT/Egg Fresh.app"
DATA_DIR="${EGG_FRESH_DATA_DIR:-$HOME/Library/Application Support/EggFresh}"
mkdir -p "$BUILD_ROOT"

cd "$PROJECT_ROOT"
# The .xcodeproj is generated and gitignored; a clean checkout won't have it.
if [[ ! -d Egg.xcodeproj ]]; then
    xcodegen generate
fi

# Same identity selection as dev.sh: a certificate-backed identity keeps the
# designated requirement stable, and ad-hoc signing is never silently used.
SIGNING_IDENTITY="${EGG_SIGNING_IDENTITY:-}"
if [[ -z "$SIGNING_IDENTITY" ]]; then
    SIGNING_IDENTITY="$(security find-identity -v -p codesigning | sed -nE 's/^[[:space:]]*[0-9]+\) ([A-F0-9]+) "Apple Development:.*$/\1/p' | head -1)"
fi
if [[ -z "$SIGNING_IDENTITY" || "$SIGNING_IDENTITY" == "-" ]]; then
    echo "A valid Apple Development signing certificate is required. Set EGG_SIGNING_IDENTITY to choose one." >&2
    exit 1
fi

echo "Building Egg (fresh profile)…"
xcodebuild -project Egg.xcodeproj -scheme Egg -configuration Debug \
    -destination 'platform=macOS,arch=arm64' -derivedDataPath "$BUILD_ROOT" \
    ARCHS=arm64 CODE_SIGN_IDENTITY="$SIGNING_IDENTITY" CODE_SIGN_STYLE=Manual DEVELOPMENT_TEAM=T53NV9W7N6 \
    SWIFT_ACTIVE_COMPILATION_CONDITIONS='DEBUG UNSIGNED_ALPHA' \
    -quiet build > "$BUILD_ROOT/fresh-build.log" 2>&1 || {
        tail -80 "$BUILD_ROOT/fresh-build.log"
        exit 1
    }

# Rebadge a copy: the fresh bundle id is what routes it around the
# single-instance guard, the shared Keychain entry, and the real defaults
# domain. Re-sign afterwards — the Info.plist edit broke the seal.
rm -rf "$FRESH_APP"
cp -R "$APP_PATH" "$FRESH_APP"
PLIST="$FRESH_APP/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier $FRESH_ID" "$PLIST"
/usr/libexec/PlistBuddy -c "Set :CFBundleName Egg Fresh" "$PLIST"
/usr/libexec/PlistBuddy -c "Set :CFBundleDisplayName Egg Fresh" "$PLIST"
codesign --force --options runtime \
    --entitlements "$PROJECT_ROOT/Egg/Egg.entitlements" \
    --sign "$SIGNING_IDENTITY" "$FRESH_APP"

# Only the fresh copy is ever stopped here; the real Egg keeps running.
pkill -f "Egg Fresh.app/Contents/MacOS/Egg" 2>/dev/null || true
sleep 0.5

if [[ $KEEP -eq 0 ]]; then
    rm -rf "$DATA_DIR"
    defaults delete "$FRESH_ID" > /dev/null 2>&1 || true
fi
mkdir -p "$DATA_DIR"

# Launched as the bare executable, not via `open`: that is what carries
# EGG_DATA_DIR into the process — `open` starts apps with a clean environment.
EGG_DATA_DIR="$DATA_DIR" "$FRESH_APP/Contents/MacOS/Egg" \
    > "$BUILD_ROOT/fresh-run.log" 2>&1 &
disown

echo "Launched Egg Fresh (data: $DATA_DIR)"
echo "The second egg in the menu bar is the fresh copy. Quit it from its own menu,"
echo "or: pkill -f 'Egg Fresh.app'"

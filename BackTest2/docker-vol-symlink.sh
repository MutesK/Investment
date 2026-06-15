#!/bin/bash

# 설정
TARGET_DIR="/mnt/nas/[App-Data]"
mkdir -p "$TARGET_DIR"

create_link() {
    local vol_name=$1
    
    # 익명 볼륨(64자리 해시)은 무시
    if [[ $vol_name =~ ^[0-9a-f]{64}$ ]]; then
        return
    fi

    # 마운트 포인트 확인
    local mountpoint=$(docker volume inspect --format '{{.Mountpoint}}' "$vol_name" 2>/dev/null)
    
    if [ -n "$mountpoint" ]; then
        # 이름 다듬기 (예: windrose_server -> Windrose-Server)
        local link_name=$(echo "$vol_name" | sed -r 's/(^|_)([a-z])/\U\2/g' | sed 's/_/-/g')
        
        ln -sfn "$mountpoint" "$TARGET_DIR/$link_name"
        echo "[$(date)] Created link: $vol_name -> $link_name"
    fi
}

remove_link() {
    local vol_name=$1
    local link_name=$(echo "$vol_name" | sed -r 's/(^|_)([a-z])/\U\2/g' | sed 's/_/-/g')
    
    if [ -L "$TARGET_DIR/$link_name" ]; then
        rm "$TARGET_DIR/$link_name"
        echo "[$(date)] Removed link: $link_name"
    fi
}

echo "Starting Docker Volume Symlink Manager..."

# 1. 기존 볼륨들 초기 동기화
for vol in $(docker volume ls -q); do
    create_link "$vol"
done

# 2. 실시간 이벤트 감시 (생성/삭제)
docker events --filter 'type=volume' --format '{{.Action}} {{.Actor.ID}}' | while read action vol; do
    if [ "$action" == "create" ]; then
        create_link "$vol"
    elif [ "$action" == "destroy" ]; then
        remove_link "$vol"
    fi
done

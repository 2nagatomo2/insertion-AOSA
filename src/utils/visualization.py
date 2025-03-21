import os

import cv2
import numpy as np
import torch
import torchvision
from cmapy import cmap
from matplotlib import pyplot as plt
import matplotlib.animation as animation
from PIL import Image


def visualize(label_name, video_maps_list, video, w=0.5, title=None, save_path=None):
    fused_list = []
    heatmap_list = []

    for frame in range(video.shape[0]):
        fused = []
        heatmap = []
        for video_maps in video_maps_list:
            _heatmap = cv2.applyColorMap(
                video_maps[frame].astype(np.uint8), cmap("jet"))
            _heatmap = _heatmap[:, :, ::-1]
            fused.append(
                cv2.addWeighted(video[frame], w, _heatmap, 1 -
                                w, 0).transpose((2, 0, 1))
            )
            heatmap.append(_heatmap.transpose(2, 0, 1))

        fused = torch.from_numpy(np.r_[fused])
        fused = torchvision.utils.make_grid(fused, ncol=1, padding=1, nrow=10).permute(
            1, 2, 0
        )

        heatmap = torch.from_numpy(np.r_[heatmap])
        heatmap = (
            torchvision.utils.make_grid(
                heatmap, ncol=1, padding=1, nrow=10)
            .permute(1, 2, 0)
            .numpy()
        )

        fused_list.append(fused)
        heatmap_list.append(heatmap)

    # for frame in range(video.shape[0]):
    #     _v_frame = np.zeros((fused.shape[0], video.shape[2]+1, 3))
    #     _v_frame[1:-1, 1:, :] = video[frame]
    #     fused_list[frame] = np.concatenate(
    #         [_v_frame, fused_list[frame]], 1).astype(np.uint8)
    #     heatmap_list[frame] = np.concatenate(
    #         [np.ones_like(_v_frame)*255, heatmap_list[frame]], 1).astype(np.uint8)

    selected_frames = [1, 5, 9, 13]  # 2枚目, 6枚目, 10枚目, 14枚目のインデックス
    num_frames = len(selected_frames)

    fig, axes = plt.subplots(3, num_frames + 1, figsize=(num_frames * 2.5, 6))  # タイトル列を追加
    plt.subplots_adjust(wspace=0.1)  # 画像間の余白を調整

    # 一番左にタイトルを表示
    if title:
        axes[0, 0].text(0.5, 0.5, "Video", fontsize=12, ha="center", va="center")
        axes[0, 0].axis("off")
        axes[1, 0].text(0.5, 0.5, f"{label_name} Map\nmask=1", fontsize=12, ha="center", va="center")
        axes[1, 0].axis("off")
        axes[2, 0].text(0.5, 0.5, f"{label_name} Map\nmasks=8", fontsize=12, ha="center", va="center")
        axes[2, 0].axis("off")
    else:
        for row in range(3):
            axes[row, 0].axis("off")

    for col, frame_idx in enumerate(selected_frames):
        # 1行目: video のフレーム
        if video.shape[1] == 3:  # (frames, channels, height, width)
            axes[0, col + 1].imshow(video[frame_idx].transpose(1, 2, 0).astype(np.uint8))
        elif video.shape[-1] == 3:  # (frames, height, width, channels)
            axes[0, col + 1].imshow(video[frame_idx].astype(np.uint8))
        else:
            raise ValueError("Unexpected shape for video: {}".format(video.shape))
        axes[0, col + 1].axis("off")

        # 2行目: video_maps_list[0] のフレーム
        if len(video_maps_list) > 0:
            axes[1, col + 1].imshow(video_maps_list[0][frame_idx], cmap="jet")
            axes[1, col + 1].axis("off")

        # 3行目: video_maps_list[1] のフレーム
        if len(video_maps_list) > 1:
            axes[2, col + 1].imshow(video_maps_list[1][frame_idx], cmap="jet")
            axes[2, col + 1].axis("off")

    plt.tight_layout()

    # 画像を保存
    plt.savefig(f"results/saliencyMaps/{label_name}.png", dpi=300)
    plt.show()

    fig, (ax1, ax2) = plt.subplots(2, 1, facecolor="white", figsize=(len(video_maps_list)*1.7,4))
    ax1.axis("off")
    ax2.axis("off")
    ims = []
    for _fused, _heatmap in zip(fused_list, heatmap_list):
        im1 = ax1.imshow(_fused, vmax=255, vmin=0, animated=True)
        im2 = ax2.imshow(_heatmap, vmax=255, vmin=0, animated=True)
        ims.append([im1, im2])

    ani = animation.ArtistAnimation(fig, ims)
    plt.close(fig)
    if title is not None:
        fig.suptitle(title)

    if save_path:
        ani.save(save_path)

    return ani.to_jshtml()

    plt.figure(figsize=(len(maps), 2))
    plt.subplot(2, 1, 1)
    plt.axis("off")
    plt.imshow(fused)
    if title is not None:
        plt.title(title)

    plt.subplot(2, 1, 2)
    plt.axis("off")
    plt.imshow(_maps[:, :, 0].astype(np.uint8), cmap="bwr", vmax=255, vmin=0)
    if title is not None:
        plt.title(title)
    plt.show()
    
    return fused, heatmap

def subplot(fig, img, n_all, n, title=None):
    ax = fig.add_subplot(1, n_all, n)
    ax.imshow(img, cmap="bwr", vmin=0, vmax=255)
    ax.tick_params(
        left=False,
        right=False,
        top=False,
        bottom=False,
        labelbottom=False,
        labelleft=False,
        labelright=False,
        labeltop=False,
    )
    if title is not None:
        ax.set_xlabel(title)


def show_maps_by_class(
    target, n, data_type, sdims=["1", "10", "0.9"], model_type="subspace"
):
    if data_type == "imagenet":
        cls_id = key_by_value(id_to_class, target)
    else:
        cls_id = target
    root = (
        "results/datasets/" + data_type + "/resnet50/" + model_type
    )

    img_root = os.path.join(root, "sdim1/org")
    path = os.path.join(img_root, cls_id, cls_id + "_" + str(n) + ".png")
    with open(path, "rb") as f:
        img = Image.open(f)
        img = img.convert("RGB")
    n_imgs = len(sdims) + 2

    fig = plt.figure(figsize=(n_imgs, 1))
    plt.axis("off")
    subplot(fig, img, n_imgs, 1, "Original")

    maps = []

    for i, dim in enumerate(sdims):
        map_root = os.path.join(root, "sdim" + dim + "/")
        ssa_map = np.load(
            os.path.join(
                map_root,
                "subs_saliency",
                cls_id,
                cls_id + "_" + str(n) + ".npy",
            )
        )
        subplot(fig, ssa_map[-1][0], n_imgs, i + 2, str(dim))
        maps.append(ssa_map[-1][0])

    map_root = os.path.join(root, "sdim1/")
    osm_map = np.load(
        os.path.join(map_root, "osm", cls_id, cls_id + "_" + str(n) + ".npy")
    )
    subplot(fig, osm_map[-1][0], n_imgs, n_imgs, "OSM")
    maps.append(osm_map[-1][0])
    return img, maps

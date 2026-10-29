/* Decode a tiny H.264 fixture through the exact bundled Vulkan stack.
 * This does not connect to a streaming host or touch an existing session. */
#include <libavcodec/avcodec.h>
#include <libavutil/hwcontext.h>
#include <stdio.h>
#include <stdlib.h>

static enum AVPixelFormat choose_format(AVCodecContext *ctx, const enum AVPixelFormat *formats)
{
    (void)ctx;
    for (; *formats != AV_PIX_FMT_NONE; formats++)
        if (*formats == AV_PIX_FMT_VULKAN) return *formats;
    return AV_PIX_FMT_NONE;
}

static int receive(AVCodecContext *ctx, AVFrame *frame, int *frames)
{
    int result;
    while ((result = avcodec_receive_frame(ctx, frame)) >= 0) {
        if (frame->format != AV_PIX_FMT_VULKAN || frame->width != 1920 || frame->height != 1080)
            return -1;
        ++*frames;
        av_frame_unref(frame);
    }
    return result == AVERROR(EAGAIN) || result == AVERROR_EOF ? 0 : result;
}

int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    FILE *file = fopen(argv[1], "rb");
    if (!file) return 2;
    fseek(file, 0, SEEK_END);
    long size = ftell(file);
    rewind(file);
    unsigned char *data = av_mallocz(size + AV_INPUT_BUFFER_PADDING_SIZE);
    if (!data || fread(data, 1, size, file) != (size_t)size) return 2;
    fclose(file);
    const AVCodec *codec = avcodec_find_decoder(AV_CODEC_ID_H264);
    AVCodecContext *ctx = avcodec_alloc_context3(codec);
    AVBufferRef *device = NULL;
    if (!ctx || av_hwdevice_ctx_create(&device, AV_HWDEVICE_TYPE_VULKAN, NULL, NULL, 0) < 0) return 3;
    ctx->hw_device_ctx = av_buffer_ref(device);
    ctx->get_format = choose_format;
    ctx->thread_count = 1;
    if (avcodec_open2(ctx, codec, NULL) < 0) return 4;
    AVPacket *packet = av_packet_alloc();
    AVFrame *frame = av_frame_alloc();
    int count = 0;
    // Upstream's minimal FFmpeg has decoders but no elementary-stream parser.
    // The fixture uses an access-unit delimiter before each complete frame,
    // matching Moonlight's complete-frame packet submission.
    long boundaries[5];
    int units = 0;
    for (long i = 0; i + 4 < size; i++) {
        int prefix = data[i] == 0 && data[i+1] == 0 && data[i+2] == 1 ? 3 :
                     data[i] == 0 && data[i+1] == 0 && data[i+2] == 0 && data[i+3] == 1 ? 4 : 0;
        if (prefix && (data[i+prefix] & 31) == 9) {
            if (units >= 4) return 5;
            boundaries[units++] = i;
        }
        if (prefix) i += prefix - 1;
    }
    if (units != 4 || boundaries[0] != 0) return 7;
    boundaries[4] = size;
    for (int i = 0; i < units; i++) {
        packet->data = data + boundaries[i];
        packet->size = boundaries[i+1] - boundaries[i];
        if (avcodec_send_packet(ctx, packet) < 0 || receive(ctx, frame, &count) < 0) return 8;
    }
    if (avcodec_send_packet(ctx, NULL) < 0 || receive(ctx, frame, &count) < 0) return 9;
    if (count != 4) return 10;
    printf("PASS: decoded %d frames at 1920x1080 using Vulkan hardware frames\n", count);
    av_frame_free(&frame);
    av_packet_free(&packet);
    avcodec_free_context(&ctx);
    av_buffer_unref(&device);
    av_free(data);
    return 0;
}

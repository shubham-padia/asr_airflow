import subprocess
import os

def merge_audio(wav_list, output_file_prefix, video_dir):
    output_audio_path = "%s/%s.wav" % (video_dir, output_file_prefix)
    merge_command = ["sox", "-m"]
    merge_command.extend(wav_list)
    merge_command.append(output_audio_path)

    subprocess.check_call(merge_command)
    return output_audio_path

def convert_to_video(input_audio_path, output_file_prefix, video_dir):
    output_file_path = "%s/%s.mp4" % (video_dir, output_file_prefix)
    conversion_command = ["ffmpeg", "-loop", "1", "-i", "dags/tasks/video_conversion_black.jpg", "-i", input_audio_path, "-c:v",
                          "libx264", "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest", output_file_path]
    
    subprocess.check_call(conversion_command)

def convert_audio_to_video(wav_list, output_file_prefix, video_dir):
    merged_audio_path = merge_audio(wav_list, output_file_prefix, video_dir)
    convert_to_video(merged_audio_path, output_file_prefix, video_dir)

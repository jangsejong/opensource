package com.blackstonedj;

import java.awt.image.BufferedImage;
import java.io.IOException;
import org.bytedeco.javacpp.avcodec;
import org.bytedeco.javacv.FFmpegFrameGrabber;
import org.bytedeco.javacv.FFmpegFrameRecorder;
import org.bytedeco.javacv.FrameGrabber.Exception;
import org.bytedeco.javacv.Java2DFrameConverter;

public class VideoFilter 
{
	private String path;
	private String outputName;
	private CannyEdge canny;
	private Pallettization pallette;
	private Combiner combine=  new Combiner();
	public VideoFilter(CannyEdge canny, Pallettization pallette, String path, String outputName)
	{
		this.path = path;
		this.outputName = outputName;
		this.canny = canny;
		this.pallette = pallette;
	}

	public void filter() throws IOException
	{
		FFmpegFrameGrabber g = new FFmpegFrameGrabber(path);
		FFmpegFrameRecorder recorder;
		int counter = 0;
		try {
			g.start();
			recorder = new FFmpegFrameRecorder(outputName+".mp4", g.getImageWidth(), g.getImageHeight());
			recorder.setVideoCodec(avcodec.AV_CODEC_ID_H264);
			recorder.setVideoBitrate(g.getVideoBitrate());
			recorder.setFrameRate(g.getFrameRate());
			recorder.setFormat("mp4");
			recorder.start();
			int frameCount = (g.getLengthInFrames());
			System.out.println("#Frames: " +frameCount);
			Java2DFrameConverter f = new Java2DFrameConverter();
			while(counter < frameCount)
			{
				try 
				{
					BufferedImage img = f.convert(g.grabImage());
					if(img != null)
					{
						recorder.record(f.convert(combine.combineImages(canny.proccessor(img), pallette.runner(img))));
					}
					counter += 1;
					System.out.println("frame: " +counter);
				} 
				
				catch (Exception e) 		
				{
					e.printStackTrace();
				}
			}
			
			recorder.stop();
			recorder.release();
			g.close();
		} 		
		catch (Exception e1) 
		{
			e1.printStackTrace();
		}  			
	}
}

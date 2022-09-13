package com.blackstonedj;
import java.awt.image.BufferedImage;
public class CannyEdge 
{
	private EdgeDetector filter;
	private GreyScale grey;
	private GaussianBlur blur;
	private DoubleThreshold thresh;
	private boolean direction = false;
	private boolean thinned = false;
	
	//constructor taking in edge filter, greyscale filter, and gaussianblur kernel
	public CannyEdge(EdgeDetector filter, GreyScale grey, GaussianBlur blur, DoubleThreshold thresh, boolean direction, boolean thinned)
	{
		this.filter    = filter;
		this.grey 	   = grey;
		this.blur      = blur;
		this.direction = direction;
		this.thinned   = thinned;
		this.thresh    = thresh;
	}
	
	//edge detection with edge thinner
	public BufferedImage proccessor(BufferedImage img)
	{
		img = grey.greyScale(img);
		img = blur.gaussianFilter(img);
		img = filter.edgeDetection(img, direction, thinned);
		img = thresh.DoubleThresholder(img, filter.getEdgeVals());
		img = thresh.hysterisis(img, filter.getMax());
		BufferedImage cI = img;
		img.flush();
		return cI;
	}

	public BufferedImage[] proccessor(BufferedImage[] imageBatch) 
	{
			for (int i = 0; i < imageBatch.length; i++)
			{
				BufferedImage img = imageBatch[i];
				img = grey.greyScale(img);
				img = blur.gaussianFilter(img);
				img = filter.edgeDetection(img, direction, thinned);
				img = thresh.DoubleThresholder(img, filter.getEdgeVals());
				imageBatch[i] = thresh.hysterisis(img, filter.getMax());
				
			}
			
			return imageBatch;
	}
}

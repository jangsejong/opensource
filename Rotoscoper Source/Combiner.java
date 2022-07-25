package com.blackstonedj;

import java.awt.Color;
import java.awt.image.BufferedImage;
import java.io.IOException;

public class Combiner 
{
	private ImageModder m = new ImageModder();
	public Combiner()
	{		
	}
	
	public BufferedImage combineImages(BufferedImage cannyImg, BufferedImage paletteImg) throws IOException
	{	
		for(int i = 0; i < cannyImg.getWidth(); i++)
		{
			for(int j = 0; j < cannyImg.getHeight(); j++)
			{
				int pixelCol = cannyImg.getRGB(i,j);
				if(pixelCol == -16777216)
				{
					paletteImg.setRGB(i, j, Color.BLACK.getRGB());
				}
			}
		}
		
		cannyImg.flush();
		return paletteImg;		
	}
	
	public BufferedImage[] combineImages(BufferedImage[] c, BufferedImage[] p)
	{
		BufferedImage[] comb = new BufferedImage[c.length];
		for(int y = 0; y< c.length; y++)
		{
			BufferedImage cannyImg = c[y];
			BufferedImage palletteImg = p[y];
			for(int i = 0; i < cannyImg.getWidth(); i++)
			{
				for(int j = 0; j < cannyImg.getHeight(); j++)
				{
					int pixelCol = cannyImg.getRGB(i,j);
					if(pixelCol == -16777216)
					{
						palletteImg.setRGB(i, j, Color.BLACK.getRGB());
					}
				}
			}
			
			comb[y] = palletteImg;
			cannyImg.flush();
			palletteImg.flush();
		}
		
		for(int t = 0; t< c.length; t++)
		{
			m.save("cm"+Integer.toString(t), comb[t]);
		}
		
		return comb;
	}
}

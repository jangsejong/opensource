package com.blackstonedj;

import java.awt.Color;
import java.awt.image.BufferedImage;

public class Circle 
{
	private int radius;
	public Circle(int radius)
	{
		this.radius = radius;
	}
	
	public BufferedImage makeCircle(int width, int height)
	{
		BufferedImage circle = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);
		int h = ((circle.getWidth()) / 2);
		int k = ((circle.getHeight()) / 2);

		for(int i = 0; i < circle.getWidth(); i++)
		{
			for(int j = 0; j < circle.getHeight(); j++)
			{
				double val = Math.pow(i - h,2) + Math.pow(j - k,2);
				if(val/4 <= radius)
				{
					System.out.println("i: " +i +", j: " +j);
					circle.setRGB(i, j, new Color(255,255,255).getRGB());
				}
				
				else
				{
					circle.setRGB(i, j, new Color(0,0,0).getRGB());
				}
			}
		}
		
		return circle;
	}
}

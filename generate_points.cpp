#include <iostream>
#include <fstream>
#include <random>
#include "cec17_test_COP.cpp"

using namespace std;
unsigned seed2 = 2024;
std::mt19937 generator_uni_r(seed2);
std::uniform_real_distribution<double> uni_real(0.0,1.0);

double Random(double minimal, double maximal){return uni_real(generator_uni_r)*(maximal-minimal)+minimal;}
void cec17_test_COP(double *x, double *f, double *g,double *h, int nx, int mx,int func_num);

const int ng_B[28]={1,1,1,2,2,0,0,0,1,0,1,2,3,1,1,1,1,2,2,2,2,3,1,1,1,1,2,2};
const int nh_B[28]={0,0,1,0,0,6,2,2,1,2,1,0,0,1,1,1,1,1,0,0,0,0,1,1,1,1,1,0};
                        //1   2   3  4  5  6  7   8  9  10  11  12  13  14  15  16  17  18 19  20  21  22  23  24  25  26  27 28
const int border[28] = {100,100,100,10,10,20,50,100,10,100,100,100,100,100,100,100,100,100,50,100,100,100,100,100,100,100,100,50};

double *OShift=NULL,*M=NULL,*M1=NULL,*M2=NULL,*y=NULL,*z=NULL,*z1=NULL,*z2=NULL;
int ini_flag=0,n_flag,func_flag,f5_flag;
int GNVars;
double tempF[1];
double tempG[3];
double tempH[6];

double cec_24_constr(double* HostVector, const int func_num)
{
    tempG[0] = 0;tempG[1] = 0;tempG[2] = 0;
    tempH[0] = 0;tempH[1] = 0;tempH[2] = 0;tempH[3] = 0;tempH[4] = 0;tempH[5] = 0;
    cec17_test_COP(HostVector, tempF, tempG, tempH, GNVars, 1, func_num);
    return tempF[0];
}

int main(int argc, char** argv)
{
    char buffer[200];
    GNVars = 30;
    double* xtmp = new double[GNVars];
    for(int func_num=1;func_num!=29;func_num++)
    {
        sprintf(buffer, "check_F%d_D%d_.txt",func_num,GNVars);
        ofstream fout(buffer);
        fout.precision(20);
        for(int j=0;j!=100;j++)
        {
            for(int k=0;k!=GNVars;k++)
                xtmp[k] = Random(-border[func_num-1],border[func_num-1]);
            cec_24_constr(xtmp, func_num);

            for(int k=0;k!=GNVars;k++)
                fout<<xtmp[k]<<"\t";
            for(int k=0;k!=3;k++)
                fout<<tempG[k]<<"\t";
            for(int k=0;k!=6;k++)
                fout<<tempH[k]<<"\t";
            fout<<tempF[0]<<endl;
        }
        cout<<func_num<<endl;
    }
    delete xtmp;
	return 0;
}
